# Optimal Model Configuration Strategy

## Latest Model Versions (2025)

### Available Models
1. **Claude Sonnet 4.5** (`claude-sonnet-4.5-20250514`)
   - Best for: Code generation, Python tasks, technical analysis
   - Strengths: Superior coding ability, precise technical execution

2. **GPT-5** (`gpt-5-latest`)
   - Best for: Complex reasoning, strategic analysis, decision-making
   - Strengths: Advanced reasoning, comprehensive analysis

3. **Gemini 2.5 Pro** (`gemini-2.5-pro-latest`)
   - Best for: Long context processing, document analysis
   - Strengths: 2M token context window, multimodal capabilities

4. **Grok 4** (`grok-4-latest`)
   - Best for: Real-time Twitter/X data, social media sentiment
   - Strengths: Access to X platform, real-time information

---

## Recommended Agent Assignments

### Coding & Python Tasks → Claude Sonnet 4.5
```yaml
agents:
  financial_analyst:
    llm: claude  # Financial calculations, Python code
  
  data_ingestion:
    llm: claude  # Data processing scripts
  
  synthesis_reporting:
    llm: claude  # Report generation code
```

### Reasoning & Strategy → GPT-5
```yaml
agents:
  project_manager:
    llm: gpt5  # Strategic coordination
  
  integration_planner:
    llm: gpt5  # Integration strategy
  
  legal_counsel:
    llm: gpt5  # Legal reasoning
  
  competitive_benchmarking:
    llm: gpt5  # Competitive analysis
  
  macroeconomic_analyst:
    llm: gpt5  # Economic reasoning
  
  external_validator:
    llm: gpt5  # Validation logic
```

### Long Context → Gemini 2.5 Pro
```yaml
agents:
  conversational_synthesis:
    llm: gemini  # Long conversation synthesis
```

### Social Media & X → Grok 4
```yaml
agents:
  market_strategist:
    llm: grok  # Market analysis with X data
    social_media_llm: grok  # Sentiment from X/Twitter
```

---

## Required settings.yaml Updates

### 1. Update AI Models Section
```yaml
ai_models:
  claude:
    model_name: "claude-sonnet-4.5-20250514"  # Updated to 4.5
    temperature: 0.1
    max_tokens: 8192
    use_cases:
      - "Code generation"
      - "Python tasks"
      - "Financial calculations"
      - "Technical analysis"
  
  gpt5:  # NEW MODEL
    model_name: "gpt-5-latest"
    temperature: 0.2
    max_tokens: 16384
    use_cases:
      - "Strategic reasoning"
      - "Complex analysis"
      - "Decision making"
      - "Legal reasoning"
  
  gemini:
    model_name: "gemini-2.5-pro-latest"  # Updated to 2.5
    temperature: 0.1
    max_tokens: 8192
    use_cases:
      - "Long context processing"
      - "Document analysis"
      - "Conversation synthesis"
  
  grok:
    model_name: "grok-4-latest"  # Updated to 4
    temperature: 0.3
    max_tokens: 4096
    use_cases:
      - "Social media analysis"
      - "Real-time X/Twitter data"
      - "Market sentiment"
```

### 2. Update Agent Assignments
```yaml
agents:
  project_manager:
    name: "Project Manager"
    role: "Workflow Coordinator"
    llm: gpt5  # CHANGED: Reasoning
    capabilities:
      - "Workflow coordination"
      - "Task prioritization"
      - "Agent orchestration"
  
  data_ingestion:
    name: "Data Ingestion Agent"
    role: "Data Collector"
    llm: claude  # CHANGED: Python/Code
    capabilities:
      - "SEC filing retrieval"
      - "Financial data collection"
      - "Document processing"
  
  financial_analyst:
    name: "Financial Analyst"
    role: "Financial Expert"
    llm: claude  # Keep: Python/Financial calculations
    capabilities:
      - "Financial statement analysis"
      - "Valuation modeling"
      - "Ratio analysis"
  
  market_strategist:
    name: "Market Strategist"
    role: "Market Analyst"
    llm: grok  # CHANGED: Market + X data
    capabilities:
      - "Competitive analysis"
      - "Market positioning"
      - "Social media sentiment"
  
  competitive_benchmarking:
    name: "Competitive Benchmarking"
    role: "Competition Analyst"
    llm: gpt5  # CHANGED: Strategic analysis
    capabilities:
      - "Peer comparison"
      - "Industry benchmarking"
      - "Performance metrics"
  
  macroeconomic_analyst:
    name: "Macroeconomic Analyst"
    role: "Economic Expert"
    llm: gpt5  # CHANGED: Economic reasoning
    capabilities:
      - "Economic trend analysis"
      - "Market conditions"
      - "Regulatory environment"
  
  integration_planner:
    name: "Integration Planner"
    role: "M&A Integration Expert"
    llm: gpt5  # CHANGED: Strategic planning
    capabilities:
      - "Integration strategy"
      - "Synergy analysis"
      - "Risk assessment"
  
  legal_counsel:
    name: "Legal Counsel"
    role: "Legal Advisor"
    llm: gpt5  # CHANGED: Legal reasoning
    capabilities:
      - "Regulatory compliance"
      - "Legal risk assessment"
      - "Contract analysis"
  
  synthesis_reporting:
    name: "Synthesis & Reporting"
    role: "Report Generator"
    llm: claude  # CHANGED: Report generation code
    capabilities:
      - "Report synthesis"
      - "Output generation"
      - "Dashboard creation"
  
  conversational_synthesis:
    name: "Conversational Synthesis"
    role: "Conversation Manager"
    llm: gemini  # Keep: Long context
    capabilities:
      - "Natural conversation"
      - "Context management"
      - "User interaction"
  
  external_validator:
    name: "External Validator"
    role: "Quality Assurance"
    llm: gpt5  # CHANGED: Validation logic
    capabilities:
      - "Analysis validation"
      - "Quality control"
      - "Accuracy verification"
```

---

## Code Changes Required

### 1. Update `src/core/llm_factory.py`

Add GPT-5 model creation:
```python
def _create_gpt5(self, config: AIModelConfig) -> BaseChatModel:
    """Create GPT-5 model instance"""
    from langchain_openai import ChatOpenAI
    
    api_key = self.config.get_api_key("openai")
    
    logger.info(f"Creating GPT-5 model: {config.model_name}")
    
    return ChatOpenAI(
        model=config.model_name,
        api_key=api_key,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout=120.0,
        max_retries=3
    )
```

Update `_create_llm` method:
```python
def _create_llm(self, model_name: str) -> BaseChatModel:
    if model_name == "claude":
        return self._create_claude(model_config)
    elif model_name == "gemini":
        return self._create_gemini(model_config)
    elif model_name == "grok":
        return self._create_grok(model_config)
    elif model_name == "gpt5":  # ADD THIS
        return self._create_gpt5(model_config)
    else:
        raise ValueError(f"Unknown model: {model_name}")
```

---

## Benefits of This Configuration

1. **Cost Optimization**: Use each model for its strengths
2. **Performance**: Right model for right task
3. **Reliability**: Claude 4.5 for critical code
4. **Intelligence**: GPT-5 for complex reasoning
5. **Context**: Gemini 2.5 Pro for long documents
6. **Real-time Data**: Grok 4 for X/Twitter insights

---

## Implementation Checklist

- [ ] Update `config/settings.yaml` with latest model versions
- [ ] Update `config/settings.yaml` agent assignments
- [ ] Add GPT-5 model creation to `src/core/llm_factory.py`
- [ ] Update `_create_llm` method to handle `gpt5`
- [ ] Test each agent with new assignments
- [ ] Verify API keys are correct in `.env`
- [ ] Monitor performance and adjust as needed
