"""
Predictive Anomaly Detection System

This module uses machine learning to detect anomalies in financial data by learning
the "normal" operating rhythm of a company. It can proactively flag developing issues
before they become major problems.

Revolutionary Capabilities:
- Learning normal operating patterns from historical data
- Real-time anomaly scoring for new data points
- Relationship modeling between financial metrics
- Early warning system for operational irregularities
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import statistics


class AnomalyDetector:
    """
    Machine learning-based anomaly detection for financial metrics.
    
    This system learns historical patterns and identifies deviations that may
    indicate operational issues, fraud, or other concerns.
    """
    
    def __init__(self):
        self.baseline_patterns = {}
        self.metric_relationships = {}
        self.trained = False
        
    def train(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train the anomaly detector on historical financial data.
        
        Args:
            historical_data: List of historical financial statements (chronological)
            
        Returns:
            Training summary
        """
        if len(historical_data) < 4:
            return {
                'success': False,
                'message': 'Insufficient historical data for training (need at least 4 periods)'
            }
        
        # Learn baseline patterns for key metrics
        self._learn_baseline_patterns(historical_data)
        
        # Learn relationships between metrics
        self._learn_metric_relationships(historical_data)
        
        self.trained = True
        
        return {
            'success': True,
            'periods_analyzed': len(historical_data),
            'metrics_profiled': len(self.baseline_patterns),
            'relationships_learned': len(self.metric_relationships),
            'timestamp': datetime.now().isoformat()
        }
        
    def detect_anomalies(
        self, 
        current_data: Dict[str, Any],
        threshold: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detect anomalies in current financial data.
        
        Args:
            current_data: Current period financial data
            threshold: Number of standard deviations for anomaly threshold (default 2.0)
            
        Returns:
            Anomaly detection results
        """
        if not self.trained:
            return {
                'error': 'Detector not trained. Call train() first.'
            }
        
        results = {
            'anomalies_detected': [],
            'relationship_violations': [],
            'overall_anomaly_score': 0.0,
            'risk_level': 'Low',
            'timestamp': datetime.now().isoformat()
        }
        
        # Check each metric for anomalies
        metric_scores = []
        for metric_name, baseline in self.baseline_patterns.items():
            if metric_name in current_data:
                current_value = current_data[metric_name]
                anomaly_info = self._check_metric_anomaly(
                    metric_name, current_value, baseline, threshold
                )
                
                if anomaly_info['is_anomaly']:
                    results['anomalies_detected'].append(anomaly_info)
                    metric_scores.append(abs(anomaly_info['z_score']))
        
        # Check relationship violations
        relationship_violations = self._check_relationship_violations(
            current_data, threshold
        )
        results['relationship_violations'] = relationship_violations
        
        # Calculate overall anomaly score
        all_scores = metric_scores + [v['severity'] for v in relationship_violations]
        if all_scores:
            results['overall_anomaly_score'] = statistics.mean(all_scores)
        
        # Determine risk level
        results['risk_level'] = self._assess_risk_level(
            results['overall_anomaly_score'],
            len(results['anomalies_detected']),
            len(results['relationship_violations'])
        )
        
        return results
        
    def _learn_baseline_patterns(self, historical_data: List[Dict[str, Any]]):
        """Learn normal patterns for each financial metric."""
        key_metrics = [
            'revenue', 'cost_of_revenue', 'gross_profit', 'operating_expenses',
            'operating_income', 'net_income', 'total_assets', 'total_liabilities',
            'total_equity', 'cash', 'inventory', 'accounts_receivable',
            'accounts_payable', 'operating_cash_flow'
        ]
        
        for metric in key_metrics:
            values = []
            for period in historical_data:
                if metric in period and period[metric] is not None:
                    values.append(float(period[metric]))
            
            if len(values) >= 4:
                self.baseline_patterns[metric] = {
                    'mean': statistics.mean(values),
                    'std': statistics.stdev(values) if len(values) > 1 else 0,
                    'min': min(values),
                    'max': max(values),
                    'median': statistics.median(values),
                    'sample_size': len(values)
                }
        
    def _learn_metric_relationships(self, historical_data: List[Dict[str, Any]]):
        """Learn typical relationships between financial metrics."""
        # Define key relationships to monitor
        relationships = [
            {
                'name': 'inventory_revenue_relationship',
                'numerator': 'inventory',
                'denominator': 'revenue',
                'description': 'Inventory as % of revenue'
            },
            {
                'name': 'ar_revenue_relationship',
                'numerator': 'accounts_receivable',
                'denominator': 'revenue',
                'description': 'AR as % of revenue (DSO proxy)'
            },
            {
                'name': 'cogs_revenue_relationship',
                'numerator': 'cost_of_revenue',
                'denominator': 'revenue',
                'description': 'COGS as % of revenue (gross margin inverse)'
            },
            {
                'name': 'opex_revenue_relationship',
                'numerator': 'operating_expenses',
                'denominator': 'revenue',
                'description': 'OpEx as % of revenue'
            },
            {
                'name': 'cash_assets_relationship',
                'numerator': 'cash',
                'denominator': 'total_assets',
                'description': 'Cash as % of assets'
            }
        ]
        
        for relationship in relationships:
            ratios = []
            for period in historical_data:
                num = period.get(relationship['numerator'])
                denom = period.get(relationship['denominator'])
                
                if num is not None and denom is not None and denom != 0:
                    ratio = float(num) / float(denom)
                    ratios.append(ratio)
            
            if len(ratios) >= 4:
                self.metric_relationships[relationship['name']] = {
                    'numerator': relationship['numerator'],
                    'denominator': relationship['denominator'],
                    'description': relationship['description'],
                    'mean': statistics.mean(ratios),
                    'std': statistics.stdev(ratios) if len(ratios) > 1 else 0,
                    'min': min(ratios),
                    'max': max(ratios),
                    'sample_size': len(ratios)
                }
        
    def _check_metric_anomaly(
        self,
        metric_name: str,
        current_value: float,
        baseline: Dict[str, Any],
        threshold: float
    ) -> Dict[str, Any]:
        """Check if a metric value is anomalous."""
        mean = baseline['mean']
        std = baseline['std']
        
        # Handle zero std (constant values)
        if std == 0:
            std = abs(mean) * 0.1 if mean != 0 else 1.0
        
        # Calculate z-score
        z_score = (current_value - mean) / std if std > 0 else 0
        
        is_anomaly = abs(z_score) > threshold
        
        # Determine direction and severity
        if z_score > threshold:
            direction = 'significantly_higher'
            severity = 'High' if z_score > 3 else 'Medium'
        elif z_score < -threshold:
            direction = 'significantly_lower'
            severity = 'High' if z_score < -3 else 'Medium'
        else:
            direction = 'normal'
            severity = 'Low'
        
        anomaly_info = {
            'metric': metric_name,
            'current_value': current_value,
            'expected_mean': mean,
            'expected_range': (mean - 2*std, mean + 2*std),
            'z_score': z_score,
            'is_anomaly': is_anomaly,
            'direction': direction,
            'severity': severity,
            'interpretation': self._interpret_metric_anomaly(
                metric_name, current_value, mean, direction
            )
        }
        
        return anomaly_info
        
    def _check_relationship_violations(
        self,
        current_data: Dict[str, Any],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Check for violations of learned metric relationships."""
        violations = []
        
        for rel_name, rel_info in self.metric_relationships.items():
            num = current_data.get(rel_info['numerator'])
            denom = current_data.get(rel_info['denominator'])
            
            if num is not None and denom is not None and denom != 0:
                current_ratio = float(num) / float(denom)
                expected_mean = rel_info['mean']
                expected_std = rel_info['std']
                
                # Handle zero std
                if expected_std == 0:
                    expected_std = abs(expected_mean) * 0.1 if expected_mean != 0 else 0.1
                
                # Calculate z-score for relationship
                z_score = (current_ratio - expected_mean) / expected_std if expected_std > 0 else 0
                
                if abs(z_score) > threshold:
                    violation = {
                        'relationship': rel_name,
                        'description': rel_info['description'],
                        'current_ratio': current_ratio,
                        'expected_ratio': expected_mean,
                        'expected_range': (
                            expected_mean - 2*expected_std,
                            expected_mean + 2*expected_std
                        ),
                        'z_score': z_score,
                        'severity': abs(z_score),
                        'interpretation': self._interpret_relationship_violation(
                            rel_name, rel_info, current_ratio, expected_mean, z_score
                        )
                    }
                    violations.append(violation)
        
        return violations
        
    def _interpret_metric_anomaly(
        self,
        metric_name: str,
        current_value: float,
        expected_value: float,
        direction: str
    ) -> str:
        """Generate human-readable interpretation of metric anomaly."""
        if direction == 'normal':
            return f"{metric_name} is within normal range"
        
        pct_diff = abs((current_value - expected_value) / expected_value * 100) if expected_value != 0 else 0
        
        interpretations = {
            'revenue': {
                'significantly_higher': f"Revenue is {pct_diff:.1f}% above historical average - possible one-time event or accelerating growth",
                'significantly_lower': f"Revenue is {pct_diff:.1f}% below historical average - WARNING: potential demand slowdown"
            },
            'inventory': {
                'significantly_higher': f"Inventory is {pct_diff:.1f}% above normal - WARNING: possible slowing sales or obsolete inventory",
                'significantly_lower': f"Inventory is {pct_diff:.1f}% below normal - possible stockout risk or improved efficiency"
            },
            'accounts_receivable': {
                'significantly_higher': f"AR is {pct_diff:.1f}% above normal - WARNING: possible collection issues or revenue recognition concerns",
                'significantly_lower': f"AR is {pct_diff:.1f}% below normal - improved collections or timing differences"
            },
            'cash': {
                'significantly_higher': f"Cash is {pct_diff:.1f}% above normal - strong liquidity position",
                'significantly_lower': f"Cash is {pct_diff:.1f}% below normal - WARNING: potential liquidity concerns"
            },
            'operating_expenses': {
                'significantly_higher': f"OpEx is {pct_diff:.1f}% above normal - WARNING: possible cost overruns or one-time charges",
                'significantly_lower': f"OpEx is {pct_diff:.1f}% below normal - improved efficiency or timing differences"
            }
        }
        
        if metric_name in interpretations and direction in interpretations[metric_name]:
            return interpretations[metric_name][direction]
        else:
            return f"{metric_name} is {direction.replace('_', ' ')}"
        
    def _interpret_relationship_violation(
        self,
        rel_name: str,
        rel_info: Dict[str, Any],
        current_ratio: float,
        expected_ratio: float,
        z_score: float
    ) -> str:
        """Generate interpretation of relationship violation."""
        direction = "higher" if z_score > 0 else "lower"
        pct_diff = abs((current_ratio - expected_ratio) / expected_ratio * 100) if expected_ratio != 0 else 0
        
        interpretations = {
            'inventory_revenue_relationship': 
                f"⚠️ Inventory-to-Revenue ratio is {pct_diff:.1f}% {direction} than normal. "
                f"This suggests {'potential overstocking or slowing sales' if z_score > 0 else 'possible stockouts or improved inventory management'}.",
            
            'ar_revenue_relationship':
                f"⚠️ AR-to-Revenue ratio is {pct_diff:.1f}% {direction} than normal. "
                f"This indicates {'potential collection issues or extended payment terms' if z_score > 0 else 'improved collections'}.",
            
            'cogs_revenue_relationship':
                f"⚠️ COGS-to-Revenue ratio is {pct_diff:.1f}% {direction} than normal. "
                f"Gross margins are {'compressing - input costs may be rising' if z_score > 0 else 'expanding - strong pricing power or cost management'}.",
            
            'opex_revenue_relationship':
                f"⚠️ OpEx-to-Revenue ratio is {pct_diff:.1f}% {direction} than normal. "
                f"Operating leverage is {'deteriorating' if z_score > 0 else 'improving'}.",
            
            'cash_assets_relationship':
                f"⚠️ Cash-to-Assets ratio is {pct_diff:.1f}% {direction} than normal. "
                f"Liquidity position is {'improving' if z_score > 0 else 'weakening'}."
        }
        
        return interpretations.get(
            rel_name,
            f"{rel_info['description']} is {pct_diff:.1f}% {direction} than historical norm"
        )
        
    def _assess_risk_level(
        self,
        anomaly_score: float,
        num_anomalies: int,
        num_violations: int
    ) -> str:
        """Assess overall risk level based on anomaly detection results."""
        total_issues = num_anomalies + num_violations
        
        if anomaly_score > 3.0 or total_issues >= 5:
            return 'Critical'
        elif anomaly_score > 2.5 or total_issues >= 3:
            return 'High'
        elif anomaly_score > 2.0 or total_issues >= 2:
            return 'Medium'
        else:
            return 'Low'
        
    def generate_early_warning_report(
        self,
        anomaly_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate an early warning report based on anomaly detection.
        
        Args:
            anomaly_results: Results from detect_anomalies()
            
        Returns:
            Early warning report with actionable insights
        """
        report = {
            'executive_summary': '',
            'critical_findings': [],
            'recommended_actions': [],
            'monitoring_priorities': [],
            'timestamp': datetime.now().isoformat()
        }
        
        risk_level = anomaly_results.get('risk_level', 'Low')
        anomalies = anomaly_results.get('anomalies_detected', [])
        violations = anomaly_results.get('relationship_violations', [])
        
        # Executive summary
        if risk_level == 'Critical':
            report['executive_summary'] = (
                f"🚨 CRITICAL ALERT: {len(anomalies)} metric anomalies and {len(violations)} "
                f"relationship violations detected. Immediate management attention required."
            )
        elif risk_level == 'High':
            report['executive_summary'] = (
                f"⚠️ HIGH RISK: Multiple anomalies detected ({len(anomalies)} metrics, {len(violations)} relationships). "
                f"Recommend detailed investigation."
            )
        elif risk_level == 'Medium':
            report['executive_summary'] = (
                f"📊 MODERATE CONCERN: Some anomalies detected. Monitor closely for trend development."
            )
        else:
            report['executive_summary'] = (
                f"✅ LOW RISK: Financial metrics within normal operating parameters."
            )
        
        # Critical findings
        for anomaly in anomalies:
            if anomaly['severity'] == 'High':
                report['critical_findings'].append({
                    'type': 'metric_anomaly',
                    'metric': anomaly['metric'],
                    'finding': anomaly['interpretation']
                })
        
        for violation in violations:
            if violation['severity'] > 2.5:
                report['critical_findings'].append({
                    'type': 'relationship_violation',
                    'relationship': violation['description'],
                    'finding': violation['interpretation']
                })
        
        # Recommended actions
        if any('inventory' in str(a).lower() for a in anomalies):
            report['recommended_actions'].append(
                "Conduct detailed inventory aging analysis to identify obsolete or slow-moving items"
            )
        
        if any('receivable' in str(a).lower() for a in anomalies):
            report['recommended_actions'].append(
                "Review AR aging report and assess collection risks by customer segment"
            )
        
        if any('cash' in str(a).lower() for a in anomalies):
            report['recommended_actions'].append(
                "Update cash flow projections and assess liquidity requirements"
            )
        
        # Monitoring priorities
        if len(anomalies) > 0:
            report['monitoring_priorities'] = [
                anomaly['metric'] for anomaly in sorted(
                    anomalies,
                    key=lambda x: abs(x['z_score']),
                    reverse=True
                )[:5]
            ]
        
        return report
