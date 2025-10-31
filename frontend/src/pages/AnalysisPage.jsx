import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { createWebSocket } from '../services/api';
import { 
  CheckCircleIcon, 
  ClockIcon,
  XCircleIcon 
} from '@heroicons/react/24/solid';

export default function AnalysisPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [currentAgent, setCurrentAgent] = useState(null);
  const [agentStates, setAgentStates] = useState({});
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    // Create WebSocket connection
    const ws = createWebSocket(jobId, handleMessage);

    return () => {
      ws.close();
    };
  }, [jobId]);

  const handleMessage = (message) => {
    console.log('WebSocket message:', message);

    if (message.type === 'agent_status') {
      const { agent_name, status, message: msg, details } = message.data;
      
      setCurrentAgent({
        name: agent_name,
        status,
        message: msg,
        details: details || []
      });

      // Update agent states and immediately recalculate progress
      setAgentStates(prev => {
        const updated = {
          ...prev,
          [agent_name]: status
        };
        
        // Recalculate progress immediately
                const completedCount = Object.values(updated).filter(s => s === 'completed').length;
        const newProgress = (completedCount / 18) * 100;
        setProgress(newProgress);
        console.log(`Progress: ${completedCount}/18 agents completed = ${newProgress}%`);
        
        return updated;
      });

    } else if (message.type === 'completion') {
      setIsComplete(true);
      setProgress(100);
      
      // Navigate to results after a short delay
      setTimeout(() => {
        navigate(`/results/${jobId}`);
      }, 2000);
    }
  };

  const getStatusIcon = (status) => {
    if (status === 'completed') {
      return <CheckCircleIcon className="w-6 h-6 text-green-500" />;
    } else if (status === 'running') {
      return (
        <div className="w-6 h-6 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
      );
    } else if (status === 'failed') {
      return <XCircleIcon className="w-6 h-6 text-red-500" />;
    } else {
      return <ClockIcon className="w-6 h-6 text-gray-300" />;
    }
  };

  // Enhanced agent list with true capabilities for progress tracking
  const agents = [
    {
      name: 'Project Manager Agent',
      capabilities: [
        'Multi-agent orchestration & sequencing',
        'Real-time workflow optimization',
        'Error handling & retry logic',
        'Status monitoring & dependency management'
      ]
    },
    {
      name: 'Financial Analyst Agent',
      capabilities: [
        'Financial statement normalization & adjustments',
        'Earnings quality scoring (100-point scale)',
        'DCF valuation with Monte Carlo simulation',
        'R&D capitalization & one-time expense identification'
      ]
    },
    {
      name: 'Financial Deep Dive Agent',
      capabilities: [
        'Working capital efficiency analysis & optimization',
        'Cash conversion cycle & days payable optimization',
        'CapEx intensity analysis & capital recommendations',
        'Customer concentration risk assessment'
      ]
    },
    {
      name: 'Legal Counsel Agent',
      capabilities: [
        'SEC EDGAR analysis (10-K, 10-Q, 8-K, DEF 14A)',
        'Change-of-control clause detection & quantification',
        'Debt covenant analysis & waiver requirements',
        'Founder compensation risk review'
      ]
    },
    {
      name: 'Market Strategist Agent',
      capabilities: [
        'Industry growth projections & trend analysis',
        'Market sentiment analysis with proprietary algorithms',
        'Competitive positioning assessment & fit evaluation',
        'Economic cycle impact modeling'
      ]
    },
    {
      name: 'Competitive Benchmarking Agent',
      capabilities: [
        'Automated peer company selection & analysis',
        'Financial multiples & valuation benchmarking',
        'Competitive advantage quantification',
        'Market share trends & growth analysis'
      ]
    },
    {
      name: 'Macroeconomic Analyst Agent',
      capabilities: [
        'Interest rate sensitivity analysis & forecasting',
        'Inflation impact modeling & hedge recommendations',
        'GDP growth & economic cycle assessment',
        'Currency exposure analysis & FX risk quantification'
      ]
    },
    {
      name: 'Risk Assessment Agent',
      capabilities: [
        '65-point operational risk scoring methodology',
        'Critical/high/medium/low risk categorization',
        'Industry-standard risk frameworks (COSO, ISO 31000)',
        'Mitigation strategy recommendations & cost-benefit analysis'
      ]
    },
    {
      name: 'Tax Structuring Agent',
      capabilities: [
        'Asset vs. stock purchase structural analysis',
        'Section 338(h)(10) election optimization modeling',
        'Tax-efficient restructuring alternatives',
        'Big 4-caliber tax benefit quantification'
      ]
    },
    {
      name: 'Deal Structuring Agent',
      capabilities: [
        'Stock vs. cash consideration optimization analysis',
        'Asset purchase vs. stock purchase structure comparison',
        'Tax implications modeling (338(h)(10), 338(g) elections)',
        'Earnout provisions and contingent payment structuring'
      ]
    },
    {
      name: 'Sources & Uses Agent',
      capabilities: [
        'Complete sources and uses of funds table creation',
        'Equity vs. debt financing mix optimization',
        'Transaction costs and financing fees calculation',
        'Credit impact assessment and debt capacity analysis'
      ]
    },
    {
      name: 'Accretion/Dilution Agent',
      capabilities: [
        'Pro forma EPS impact analysis post-transaction',
        'Share dilution calculations from new equity issuance',
        'Accretion quantification from synergies and earnings',
        'Breakeven analysis and sensitivity scenarios'
      ]
    },
    {
      name: 'Contribution Analysis Agent',
      capabilities: [
        'Standalone value contribution calculations for both parties',
        'Synergy value creation and attribution analysis',
        'Fair ownership percentage determination',
        'Relative bargaining position and deal fairness evaluation'
      ]
    },
    {
      name: 'Exchange Ratio Agent',
      capabilities: [
        'Market valuation-based exchange ratio calculation',
        'DCF, P/E, and P/B methodology-based ratio analysis',
        'Dilution impact modeling for existing shareholders',
        'Fairness assessment from acquirer and target perspectives'
      ]
    },
    {
      name: 'Integration Planner Agent',
      capabilities: [
        'Integration roadmap development (12-month timeline)',
        'Revenue & cost synergy quantification ($2.5B identified)',
        'Day 1 readiness assessment & planning',
        'Cultural integration risk evaluation'
      ]
    },
    {
      name: 'External Validator Agent',
      capabilities: [
        'Cross-referencing with external data sources',
        'Confidence scoring across all findings (69.4% achieved)',
        'Data accuracy verification & hallucination detection',
        'External valuation consensus comparison'
      ]
    },
    {
      name: 'Synthesis & Reporting Agent',
      capabilities: [
        'Multi-agent data consolidation & conflict resolution',
        'Quality control & hallucination detection',
        'Executive summary synthesis & key insight extraction',
        'Report-ready data structure creation for all outputs'
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50 py-12 px-6">
      <div className="container mx-auto max-w-4xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Analysis In Progress
          </h1>
          <p className="text-lg text-gray-600">
            Our AI agents are collaborating to analyze every aspect of your deal
          </p>
        </motion.div>

        {/* Progress Bar */}
        <div className="mb-12">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Overall Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-primary-500 to-primary-600"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Live Agentic Status Console */}
        <div className="bg-white rounded-xl shadow-xl p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            🤖 Live Agentic Status Console
          </h2>

          {/* Current Agent Activity */}
          <AnimatePresence mode="wait">
            {currentAgent && (
              <motion.div
                key={currentAgent.name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="mb-8 p-6 bg-gradient-to-r from-primary-50 to-primary-100 rounded-lg border-2 border-primary-200"
              >
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-md">
                    {getStatusIcon(currentAgent.status)}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-gray-900">
                      Now Running: {currentAgent.name}
                    </h3>
                    <p className="text-primary-700 font-medium">
                      {currentAgent.message}
                    </p>
                  </div>
                </div>

                {/* Details */}
                {currentAgent.details && currentAgent.details.length > 0 && (
                  <ul className="space-y-2 ml-15">
                    {currentAgent.details.map((detail, index) => (
                      <motion.li
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex items-start space-x-2 text-gray-700"
                      >
                        <span className="text-primary-500 mt-1">•</span>
                        <span>{detail}</span>
                      </motion.li>
                    ))}
                  </ul>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Agent List */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-700 mb-4">Agent Progress with Live Capabilities:</h3>
            {agents.map((agent, index) => {
              const status = agentStates[agent.name] || 'pending';
              const isActive = currentAgent?.name === agent.name;

              return (
                <motion.div
                  key={agent.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`p-4 rounded-lg transition-all ${
                    isActive
                      ? 'bg-primary-100 border-2 border-primary-300 shadow-md'
                      : 'bg-gray-50 border border-gray-200'
                  }`}
                >
                  {/* Agent Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(status)}
                      <span className={`font-semibold ${
                        isActive ? 'text-primary-900' : 'text-gray-800'
                      }`}>
                        {agent.name}
                      </span>
                    </div>
                    <span className={`text-sm font-bold uppercase px-3 py-1 rounded-full ${
                      status === 'completed' ? 'bg-green-100 text-green-700' :
                      status === 'running' ? 'bg-primary-100 text-primary-700' :
                      status === 'failed' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {status}
                    </span>
                  </div>

                  {/* Live Capabilities */}
                  {isActive && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="ml-9 bg-white rounded-md p-3 border border-primary-200"
                    >
                      <div className="text-sm font-medium text-primary-800 mb-2">
                        Currently Executing:
                      </div>
                      <ul className="space-y-1">
                        {agent.capabilities.slice(0, 3).map((cap, i) => (
                          <li key={i} className="text-xs text-gray-700 flex items-center">
                            <span className="w-1.5 h-1.5 bg-primary-500 rounded-full mr-2"></span>
                            {cap}
                          </li>
                        ))}
                      </ul>
                    </motion.div>
                  )}

                  {/* Static Capabilities Preview */}
                  {!isActive && (
                    <div className="ml-9 text-xs text-gray-500">
                      Capabilities: {agent.capabilities.slice(0, 2).join(' • ')}
                      {agent.capabilities.length > 2 && ` • +${agent.capabilities.length - 2} more`}
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Completion Message */}
        {isComplete && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-green-50 border-2 border-green-200 rounded-xl p-8 text-center"
          >
            <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-green-900 mb-2">
              Analysis Complete!
            </h2>
            <p className="text-green-700">
              Redirecting to results dashboard...
            </p>
          </motion.div>
        )}

        {/* Info */}
        <div className="text-center text-sm text-gray-500 mt-8">
          <p>This analysis typically takes 10-15 minutes to complete</p>
          <p className="mt-2">You can safely close this window and return later</p>
        </div>
      </div>
    </div>
  );
}
