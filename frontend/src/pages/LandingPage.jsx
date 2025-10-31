import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ChartBarIcon, 
  ShieldCheckIcon, 
  ClockIcon, 
  DocumentCheckIcon 
} from '@heroicons/react/24/outline';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50">
      {/* Header */}
      <header className="container mx-auto px-6 py-6">
        <div className="flex justify-between items-center">
          <div className="text-2xl font-bold text-primary-600">
            M&A Diligence Swarm
          </div>
          <Link
            to="/login"
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Sign In
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-4xl mx-auto"
        >
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            AI-Powered M&A
            <span className="text-primary-600"> Due Diligence</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Comprehensive, autonomous financial analysis powered by advanced AI agents. 
            Get investment-banking quality due diligence in hours, not weeks.
          </p>
          <Link
            to="/login"
            className="inline-block px-8 py-4 bg-primary-600 text-white text-lg font-semibold rounded-lg hover:bg-primary-700 transition-colors shadow-lg"
          >
            Start Analysis
          </Link>
        </motion.div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-center"
          >
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <DocumentCheckIcon className="w-8 h-8 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">1. Input Deal Details</h3>
            <p className="text-gray-600">
              Simply enter the target and acquirer tickers, deal type, and basic thesis
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-center"
          >
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <ClockIcon className="w-8 h-8 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">2. AI Agents Analyze</h3>
            <p className="text-gray-600">
              Watch as 9 specialized AI agents collaborate to analyze every aspect of the deal
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="text-center"
          >
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <ChartBarIcon className="w-8 h-8 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">3. Get Comprehensive Reports</h3>
            <p className="text-gray-600">
              Download executive summaries, financial models, and full due diligence reports
            </p>
          </motion.div>
        </div>
      </section>

      {/* Capabilities */}
      <section className="bg-white py-16">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">Capabilities</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {[
              'DCF & Comparable Valuation Models',
              'Financial Statement Analysis',
              'Legal & Regulatory Risk Assessment',
              'Competitive Landscape Analysis',
              'Market Positioning & Strategy',
              'Integration Roadmap Planning',
              'Macroeconomic Scenario Analysis',
              'External Validator Consensus Check',
              'Comprehensive Report Generation'
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg"
              >
                <ShieldCheckIcon className="w-6 h-6 text-primary-600 flex-shrink-0" />
                <span className="text-gray-700">{item}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Data Sources */}
      <section className="container mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold text-center mb-8">Powered By Public Data</h2>
        <div className="flex flex-wrap justify-center gap-8 items-center max-w-3xl mx-auto">
          <div className="text-center">
            <div className="text-xl font-semibold text-gray-700">SEC EDGAR</div>
            <p className="text-sm text-gray-500">10-K, 10-Q, 8-K Filings</p>
          </div>
          <div className="text-center">
            <div className="text-xl font-semibold text-gray-700">Financial Modeling Prep</div>
            <p className="text-sm text-gray-500">Real-time Financial Data</p>
          </div>
          <div className="text-center">
            <div className="text-xl font-semibold text-gray-700">Public Filings</div>
            <p className="text-sm text-gray-500">Comprehensive Coverage</p>
          </div>
        </div>
      </section>

      {/* Security & Compliance */}
      <section className="bg-gray-900 text-white py-16">
        <div className="container mx-auto px-6 text-center">
          <ShieldCheckIcon className="w-12 h-12 mx-auto mb-4 text-primary-400" />
          <h2 className="text-2xl font-bold mb-4">Security & Compliance</h2>
          <p className="text-gray-300 max-w-2xl mx-auto">
            All data is processed securely. We use industry-standard encryption and 
            authentication. Your analysis data is private and never shared.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-50 py-8">
        <div className="container mx-auto px-6 text-center text-gray-600">
          <p>&copy; 2025 M&A Diligence Swarm. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
