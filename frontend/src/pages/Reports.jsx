import { useState, useEffect } from "react";
import { FiDownload, FiFileText, FiSearch, FiDatabase } from "react-icons/fi";
import apiService from "../api/api";

export default function Reports() {
  const [products, setProducts] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  // Track per-product, per-format download loading state: { "productId-format": true }
  const [downloading, setDownloading] = useState({});
  const [downloadError, setDownloadError] = useState(null);

  useEffect(() => {
    apiService
      .getProducts(0, 100, "created_at", "desc")
      .then((res) => {
        setProducts(res.data || []);
      })
      .catch((err) => {
        console.error("Error loading products for reports list", err);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const filtered = products.filter(
    (p) =>
      p.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.brand && p.brand.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  /**
   * Download a report file using fetch + Blob URL approach.
   * This is more reliable than window.open() because:
   *  - It is not subject to popup blockers
   *  - It correctly forwards the auth token
   *  - It creates a named file download in the browser
   */
  const handleDownload = async (productId, format) => {
    const key = `${productId}-${format}`;
    setDownloading((prev) => ({ ...prev, [key]: true }));
    setDownloadError(null);

    try {
      const urlMap = {
        csv: apiService.getExportCsvUrl(productId),
        excel: apiService.getExportExcelUrl(productId),
        pdf: apiService.getExportPdfUrl(productId),
      };
      const extMap = { csv: ".csv", excel: ".xlsx", pdf: ".pdf" };
      const url = urlMap[format];

      const token = localStorage.getItem("token");
      const response = await fetch(url, {
        method: "GET",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          Accept: "*/*",
        },
      });

      if (!response.ok) {
        const detail = await response.text().catch(() => response.statusText);
        throw new Error(`Server returned ${response.status}: ${detail}`);
      }

      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `Reviews_Report_${productId}${extMap[format]}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error(`Download failed (${format}):`, err);
      setDownloadError(`Download failed: ${err.message}`);
      setTimeout(() => setDownloadError(null), 5000);
    } finally {
      setDownloading((prev) => ({ ...prev, [key]: false }));
    }
  };

  const isDownloading = (productId, format) =>
    downloading[`${productId}-${format}`] === true;

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 w-full flex-1 flex flex-col gap-6">
      {/* Title */}
      <div>
        <h1 className="page-title text-[#e8eaf6] flex items-center gap-2">
          <FiFileText className="text-[#3361ff]" /> Export Summaries and Reports
        </h1>
        <p className="text-sm text-[#8892b0] mt-1">
          Export scraped product reviews and computed consensus sentiment weights in tabular
          (CSV/Excel) or document formats (PDF).
        </p>
      </div>

      {/* Error banner */}
      {downloadError && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-sm text-red-400">
          <span>⚠️</span> {downloadError}
        </div>
      )}

      {/* Search Input bar */}
      <div className="card flex items-center gap-3 bg-[#161b27] border-[rgba(255,255,255,0.06)] p-3">
        <FiSearch className="text-xl text-[#8892b0] ml-2" />
        <input
          type="text"
          className="bg-transparent border-none outline-none w-full text-xs text-[#e8eaf6] placeholder-[#8892b0]"
          placeholder="Filter report listings by product title, brand or category name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Grid listing */}
      {isLoading ? (
        <div className="flex flex-col gap-4 animate-pulse">
          {[1, 2, 3].map((n) => (
            <div key={n} className="card h-20 bg-[#1c2333]"></div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="card text-center py-16 flex flex-col items-center justify-center gap-3">
          <FiDatabase className="text-4xl text-[#8892b0]" />
          <h3 className="text-lg font-semibold text-[#e8eaf6]">
            No tracked products matching query
          </h3>
          <p className="text-xs text-[#8892b0] max-w-sm">
            Import a product using its Amazon/Flipkart URL on the Home Hub, then generate reports.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {filtered.map((prod) => (
            <div
              key={prod.id}
              className="card bg-[#161b27] border-[rgba(255,255,255,0.06)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 hover:border-[#3361ff]/30 transition-all duration-200"
            >
              {/* Product Info */}
              <div className="flex flex-col gap-1 min-w-0 pr-4">
                <div className="flex items-center gap-2">
                  <span className="capitalize text-[10px] font-semibold bg-[#1c2333] px-2 py-0.5 rounded text-[#8892b0]">
                    {prod.source}
                  </span>
                  <span className="text-[10px] text-[#8892b0] font-medium">
                    {prod.brand || "Generic"}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-[#e8eaf6] truncate leading-tight mt-1">
                  {prod.product_name}
                </h3>
                <span className="text-[10px] text-[#8892b0] mt-0.5 block">
                  Reviews logged:{" "}
                  <span className="font-semibold text-[#e8eaf6]">{prod.total_reviews}</span>
                </span>
              </div>

              {/* Download buttons */}
              <div className="flex flex-wrap items-center gap-2.5 w-full sm:w-auto">
                {/* CSV */}
                <button
                  onClick={() => handleDownload(prod.id, "csv")}
                  disabled={isDownloading(prod.id, "csv")}
                  className="btn-primary text-xs px-3.5 py-2.5 rounded-xl border border-[rgba(255,255,255,0.06)] bg-[#1c2333] hover:bg-[#212840] flex-1 sm:flex-initial disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-1.5 justify-center"
                >
                  {isDownloading(prod.id, "csv") ? (
                    <span className="inline-block animate-spin">⟳</span>
                  ) : (
                    <FiDownload />
                  )}
                  CSV Data
                </button>

                {/* Excel */}
                <button
                  onClick={() => handleDownload(prod.id, "excel")}
                  disabled={isDownloading(prod.id, "excel")}
                  className="btn-primary text-xs px-3.5 py-2.5 rounded-xl border border-[rgba(255,255,255,0.06)] bg-[#1c2333] hover:bg-[#212840] flex-1 sm:flex-initial disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-1.5 justify-center"
                >
                  {isDownloading(prod.id, "excel") ? (
                    <span className="inline-block animate-spin">⟳</span>
                  ) : (
                    <FiDownload />
                  )}
                  Excel Sheet
                </button>

                {/* PDF */}
                <button
                  onClick={() => handleDownload(prod.id, "pdf")}
                  disabled={isDownloading(prod.id, "pdf")}
                  className="btn-primary text-xs px-3.5 py-2.5 rounded-xl bg-[#3361ff] flex-1 sm:flex-initial disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-1.5 justify-center"
                >
                  {isDownloading(prod.id, "pdf") ? (
                    <span className="inline-block animate-spin">⟳</span>
                  ) : (
                    <FiDownload />
                  )}
                  PDF Report
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
