import { FiAward, FiCpu, FiMessageSquare, FiTrendingUp } from "react-icons/fi";

export default function About() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-12 flex flex-col gap-8 w-full flex-1">
      {/* Title */}
      <div className="border-b border-[rgba(255,255,255,0.05)] pb-4 text-center">
        <h1 className="page-title text-[#e8eaf6]">About SentimentLens Engine</h1>
        <p className="text-sm text-[#8892b0] mt-2">
          How our dual-engine sentiment analysis and scraper pipeline works under the hood.
        </p>
      </div>

      {/* Grid Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-2">
        <div className="card bg-[#161b27] border-[rgba(255,255,255,0.06)] p-6 flex flex-col gap-3">
          <div className="bg-[#22c55e]/10 text-[#22c55e] p-3 rounded-xl w-fit text-xl">
            <FiCpu />
          </div>
          <h3 className="section-title text-[#e8eaf6]">VADER Sentiment Engine</h3>
          <p className="text-xs text-[#8892b0] leading-relaxed">
            VADER (Valence Aware Dictionary and sEntiment Reasoner) is a rule-based sentiment analysis model specifically attuned to sentiments expressed in social media, product reviews, and other short texts. 
            It automatically handles intensifiers (like "very", "extremely"), punctuation ("!!!"), contractions, and emojis.
          </p>
        </div>

        <div className="card bg-[#161b27] border-[rgba(255,255,255,0.06)] p-6 flex flex-col gap-3">
          <div className="bg-[#3361ff]/10 text-[#3361ff] p-3 rounded-xl w-fit text-xl">
            <FiAward />
          </div>
          <h3 className="section-title text-[#e8eaf6]">TextBlob Lexicon Engine</h3>
          <p className="text-xs text-[#8892b0] leading-relaxed">
            TextBlob computes sentiment scores based on an internal linguistic dictionary. It calculates:
            <br />
            • <span className="font-semibold text-[#e8eaf6]">Polarity:</span> Score between -1 (negative) and +1 (positive).
            <br />
            • <span className="font-semibold text-[#e8eaf6]">Subjectivity:</span> Score between 0 (objective fact) and 1 (subjective personal opinion).
          </p>
        </div>
      </div>

      {/* Process pipeline mapping */}
      <div className="card bg-[#161b27] border-[rgba(255,255,255,0.06)] p-6 flex flex-col gap-4">
        <h3 className="section-title text-[#e8eaf6] flex items-center gap-2">
          <FiTrendingUp className="text-[#3361ff]" /> Decision-Consensus Mechanism
        </h3>
        <p className="text-xs text-[#8892b0] leading-relaxed">
          Because lexicon engines can occasionally differ on complex or sarcastic sentences, our Combined Analyzer implements a weighted consensus mechanism.
        </p>
        <div className="bg-[#1c2333] p-4 rounded-xl border border-[rgba(255,255,255,0.03)] text-xs text-[#e8eaf6] leading-relaxed">
          <span className="font-semibold text-[#3361ff] block mb-1">Agreement Rule:</span>
          If VADER and TextBlob agree on the classification, we immediately assign that label. If they disagree, we dynamically calculate and compare the confidence strength of VADER (absolute compound value) and TextBlob (absolute polarity strength), choosing the sentiment class with the highest score.
        </div>
      </div>
    </div>
  );
}
