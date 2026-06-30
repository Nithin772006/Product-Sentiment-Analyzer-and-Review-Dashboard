import LoadingSpinner from "./LoadingSpinner";

export default function Loader({ size = "md", message, fullPage }) {
  if (fullPage) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0f1117]/80 backdrop-blur-sm">
        <LoadingSpinner size="lg" message={message || "Loading content..."} />
      </div>
    );
  }
  return <LoadingSpinner size={size} message={message} />;
}
