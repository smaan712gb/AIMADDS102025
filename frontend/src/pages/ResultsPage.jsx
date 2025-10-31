import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { analysisAPI } from '../services/api';
import Chat from '../components/Chat';
import { 
  DocumentArrowDownIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';

export default function ResultsPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadResults();
  }, [jobId]);

  const loadResults = async () => {
    try {
      const data = await analysisAPI.getResult(jobId);
      setResult(data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading results:', error);
      setLoading(false);
    }
  };

  const handleDownload = async (fileType) => {
    try {
      await analysisAPI.downloadReport(jobId, fileType);
    } catch (error) {
      console.error('Error downloading report:', error);
      alert('Failed to download report');
    }
  };

  const formatCurrency = (value) => {
    if (!value) return 'N/A';
    return `$${(value / 1000000000).toFixed(2)}B`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading results...</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Results not found</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="mt-4 btn-primary"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-6">
      <div className="container mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeftIcon className="w-5 h-5" />
            <span>Back to Dashboard</span>
          </button>
          <h1 className="text-4xl font-bold text-gray-900">Analysis Complete</h1>
          <p className="text-gray-600 mt-2">{result.project_name}</p>
        </div>

        {/* Success Banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-green-50 border-2 border-green-200 rounded-xl p-6 mb-8"
        >
          <div className="flex items-center space-x-3">
            <CheckCircleIcon className="w-8 h-8 text-green-500 flex-shrink-0" />
            <div>
              <h2 className="text-xl font-bold text-green-900">Analysis Complete!</h2>
              <p className="text-green-700">
                Comprehensive due diligence analysis has been completed successfully
              </p>
            </div>
          </div>
        </motion.div>


        {/* M&A Copilot Chat */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mb-8"
        >
          <h3 className="text-2xl font-bold text-gray-900 mb-4">Ask the M&A Copilot</h3>
          <div style={{ height: '600px' }}>
            <Chat jobId={jobId} projectName={result.project_name} />
          </div>
        </motion.div>

        {/* M&A Transaction Reports Section - Only show if M&A reports were generated */}
        {result.reports && (result.reports.ma_ic_memo || result.reports.ma_financial_model || result.reports.ma_board_deck) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl shadow-xl p-8 mb-8 border-2 border-emerald-300"
          >
            <div className="flex items-center space-x-3 mb-4">
              <span className="text-4xl">💼</span>
              <div>
                <h3 className="text-2xl font-bold text-gray-900">M&A Transaction Reports</h3>
                <p className="text-gray-600">Professional Investment Banking Deliverables</p>
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4 mb-6">
              <p className="text-sm text-gray-700">
                <strong>Investment Banking Quality:</strong> These reports provide comprehensive M&A analysis including 
                accretion/dilution, sources & uses, contribution analysis, and exchange ratio fairness. All calculations 
                use real-time market data and validated financial statements.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-4">
              {/* IC Memorandum */}
              {result.reports.ma_ic_memo && (
                <button
                  onClick={() => handleDownload('ma_ic_memo')}
                  className="flex flex-col items-center justify-center p-6 bg-white border-2 border-emerald-300 rounded-lg hover:border-emerald-600 hover:shadow-lg transition-all"
                >
                  <DocumentArrowDownIcon className="w-12 h-12 text-emerald-600 mb-3" />
                  <span className="font-bold text-gray-900 mb-1">IC Memorandum</span>
                  <span className="text-sm text-gray-600 mb-2">15-20 Pages</span>
                  <div className="text-xs text-gray-500 text-left w-full">
                    <div>✓ Executive Summary</div>
                    <div>✓ Transaction Overview</div>
                    <div>✓ Financial Analysis</div>
                    <div>✓ Risk Assessment</div>
                  </div>
                </button>
              )}

              {/* Financial Model */}
              {result.reports.ma_financial_model && (
                <button
                  onClick={() => handleDownload('ma_financial_model')}
                  className="flex flex-col items-center justify-center p-6 bg-white border-2 border-teal-300 rounded-lg hover:border-teal-600 hover:shadow-lg transition-all"
                >
                  <DocumentArrowDownIcon className="w-12 h-12 text-teal-600 mb-3" />
                  <span className="font-bold text-gray-900 mb-1">Financial Model</span>
                  <span className="text-sm text-gray-600 mb-2">Excel (7 Tabs)</span>
                  <div className="text-xs text-gray-500 text-left w-full">
                    <div>✓ Accretion/Dilution</div>
                    <div>✓ Sources & Uses</div>
                    <div>✓ Deal Structure</div>
                    <div>✓ Pro Forma Analysis</div>
                  </div>
                </button>
              )}

              {/* Board Deck */}
              {result.reports.ma_board_deck && (
                <button
                  onClick={() => handleDownload('ma_board_deck')}
                  className="flex flex-col items-center justify-center p-6 bg-white border-2 border-cyan-300 rounded-lg hover:border-cyan-600 hover:shadow-lg transition-all"
                >
                  <DocumentArrowDownIcon className="w-12 h-12 text-cyan-600 mb-3" />
                  <span className="font-bold text-gray-900 mb-1">Board Presentation</span>
                  <span className="text-sm text-gray-600 mb-2">PowerPoint (7 Slides)</span>
                  <div className="text-xs text-gray-500 text-left w-full">
                    <div>✓ Transaction Highlights</div>
                    <div>✓ Financial Impact</div>
                    <div>✓ Valuation & Fairness</div>
                    <div>✓ Recommendation</div>
                  </div>
                </button>
              )}
            </div>

            {/* M&A Analysis Summary */}
            {result.ma_analysis && (
              <div className="mt-6 bg-white rounded-lg p-6">
                <h4 className="text-lg font-bold text-gray-900 mb-4">Transaction Summary</h4>
                <div className="grid md:grid-cols-2 gap-4">
                  {result.ma_analysis.eps_impact && (
                    <div className="flex items-center space-x-3">
                      <ChartBarIcon className="w-6 h-6 text-emerald-600" />
                      <div>
                        <p className="text-sm text-gray-600">EPS Impact</p>
                        <p className="font-bold text-gray-900">
                          {result.ma_analysis.eps_impact.type} {result.ma_analysis.eps_impact.percent > 0 ? '+' : ''}{result.ma_analysis.eps_impact.percent.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  )}
                  {result.ma_analysis.transaction_size && (
                    <div className="flex items-center space-x-3">
                      <ChartBarIcon className="w-6 h-6 text-teal-600" />
                      <div>
                        <p className="text-sm text-gray-600">Transaction Size</p>
                        <p className="font-bold text-gray-900">{formatCurrency(result.ma_analysis.transaction_size)}</p>
                      </div>
                    </div>
                  )}
                  {result.ma_analysis.leverage !== undefined && (
                    <div className="flex items-center space-x-3">
                      <ChartBarIcon className="w-6 h-6 text-cyan-600" />
                      <div>
                        <p className="text-sm text-gray-600">Pro Forma Leverage</p>
                        <p className="font-bold text-gray-900">{result.ma_analysis.leverage.toFixed(2)}x</p>
                      </div>
                    </div>
                  )}
                  {result.ma_analysis.fairness && (
                    <div className="flex items-center space-x-3">
                      <CheckCircleIcon className="w-6 h-6 text-green-600" />
                      <div>
                        <p className="text-sm text-gray-600">Fairness Assessment</p>
                        <p className="font-bold text-gray-900">{result.ma_analysis.fairness}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Revolutionary Reports Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl shadow-xl p-8 mb-8 border-2 border-blue-200"
        >
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-4xl">🚀</span>
            <div>
              <h3 className="text-2xl font-bold text-gray-900">Revolutionary "Glass Box" Reports</h3>
              <p className="text-gray-600">Powered by 13 AI Specialist Agents - Superior to Traditional Analysis</p>
            </div>
          </div>
          
          <div className="bg-white rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-700">
              <strong>Why Revolutionary:</strong> Unlike traditional "black box" banker reports, 
              these showcase complete transparency with agent attribution, statistical rigor, 
              and auditable evidence. Every number traceable to SEC filings.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            {/* Revolutionary Excel */}
            <button
              onClick={() => handleDownload('revolutionary_excel')}
              className="flex flex-col items-center justify-center p-6 bg-white border-2 border-blue-300 rounded-lg hover:border-blue-600 hover:shadow-lg transition-all"
            >
              <DocumentArrowDownIcon className="w-12 h-12 text-blue-600 mb-3" />
              <span className="font-bold text-gray-900 mb-1">Glass Box Excel</span>
              <span className="text-sm text-gray-600 mb-2">12 Worksheets</span>
              <div className="text-xs text-gray-500 text-left w-full">
                <div>✓ Control Panel</div>
                <div>✓ Normalization Ledger</div>
                <div>✓ Anomaly Log</div>
                <div>✓ Legal Risk Register</div>
              </div>
            </button>

            {/* Revolutionary PowerPoint */}
            <button
              onClick={() => handleDownload('revolutionary_ppt')}
              className="flex flex-col items-center justify-center p-6 bg-white border-2 border-purple-300 rounded-lg hover:border-purple-600 hover:shadow-lg transition-all"
            >
              <DocumentArrowDownIcon className="w-12 h-12 text-purple-600 mb-3" />
              <span className="font-bold text-gray-900 mb-1">C-Suite PowerPoint</span>
              <span className="text-sm text-gray-600 mb-2">21 Slides</span>
              <div className="text-xs text-gray-500 text-left w-full">
                <div>✓ Agent Attribution</div>
                <div>✓ Critical Anomalies</div>
                <div>✓ Legal Discoveries</div>
                <div>✓ Auto-Generated Agenda</div>
              </div>
            </button>

            {/* Revolutionary PDF */}
            <button
              onClick={() => handleDownload('revolutionary_pdf')}
              className="flex flex-col items-center justify-center p-6 bg-white border-2 border-red-300 rounded-lg hover:border-red-600 hover:shadow-lg transition-all"
            >
              <DocumentArrowDownIcon className="w-12 h-12 text-red-600 mb-3" />
              <span className="font-bold text-gray-900 mb-1">Diligence Bible PDF</span>
              <span className="text-sm text-gray-600 mb-2">35+ Pages</span>
              <div className="text-xs text-gray-500 text-left w-full">
                <div>✓ Embedded Evidence</div>
                <div>✓ SEC References</div>
                <div>✓ Agent Collaboration</div>
                <div>✓ Full Transparency</div>
              </div>
            </button>
          </div>

          {/* Embedded Agentic Insights Dashboard */}
          <div className="mt-8">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-xl font-bold text-gray-900">Interactive Agentic Insights Dashboard</h4>
              <a 
                href="http://localhost:8050" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                Open in new tab →
              </a>
            </div>
            <div className="bg-white rounded-lg p-2 shadow-inner">
              <iframe 
                src="http://localhost:8050"
                className="w-full h-[700px] border-2 border-gray-200 rounded-lg"
                title="Agentic Insights Dashboard"
                style={{minHeight: '700px', maxHeight: '800px'}}
              />
            </div>
          </div>
        </motion.div>

        {/* Standard Reports Section - Removed in favor of Revolutionary reports */}

        {/* Footer Actions */}
        <div className="mt-8 flex justify-center">
          <button
            onClick={() => navigate('/dashboard')}
            className="btn-primary"
          >
            Start New Analysis
          </button>
        </div>
      </div>
    </div>
  );
}
