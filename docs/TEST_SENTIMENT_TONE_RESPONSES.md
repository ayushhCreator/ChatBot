# Testing: Sentiment-Aware Responses

## Quick Test Scenarios

Run the conversation simulator and observe response lengths:

### Scenario 1: Angry Customer

```bash
Turn: "That's too much"
Expected:
  - SentimentToneAnalyzer output: anger=8, tone="Direct, solution-focused, brief", max_sentences=2
  - Response: 1-2 sentences, offers cheapest option

Example response:
  "Our Basic plan is ₹299. Would that work for you?"

Previous (wrong):
  "I understand why you might feel that way—service selection can feel
   overwhelming. Let's simplify this: are there specific services you're
   interested in, or would you like to narrow down options based on your
   needs? I'm here to help—let me know how I can assist further!"
```

### Scenario 2: Bored Customer

```bash
Turn: "meh"
Expected:
  - SentimentToneAnalyzer output: boredom=7, tone="Engaging, conversational, quick", max_sentences=3
  - Response: 2-3 sentences, interesting angle, tries to re-engage

Example response:
  "Our premium package is seriously impressive—full detailing, ceramic
   coating, the works. Want to hear what's included?"
```

### Scenario 3: Interested Customer

```bash
Turn: "Tell me more about your premium service"
Expected:
  - SentimentToneAnalyzer output: interest=8, tone="Enthusiastic, detailed, helpful", max_sentences=4
  - Response: 3-4 sentences, detailed, encourages further exploration

Example response:
  "Great question! Our premium service includes hand wash, interior vacuum,
   leather conditioning, and ceramic coating. The ceramic creates a
   protective layer that lasts 6+ months. Interested in booking?"
```

---

## Verification Checklist

After running tests:

- [ ] Angry customer responses are shorter (1-2 sentences)
- [ ] Interested customer responses are longer (3-4 sentences)
- [ ] Bored customer responses try to re-engage (interesting angles)
- [ ] DEBUG logs show `🎯 TONE ANALYSIS:` messages
- [ ] No 4-5 sentence responses for angry customers (like before)
- [ ] LLM call count/tokens look reasonable

---

## Log Inspection

Enable DEBUG logging and look for:

```bash
🎯 TONE ANALYSIS: tone='Direct, solution-focused, brief' max_sentences=2
🎯 TONE ANALYSIS: tone='Engaging, conversational, quick' max_sentences=3
🎯 TONE ANALYSIS: tone='Enthusiastic, detailed, helpful' max_sentences=4
🎯 TONE ANALYSIS: tone='Professional, helpful, clear' max_sentences=3
```

---

## Metrics to Measure

1. **Token Efficiency**: Count LLM tokens before/after
2. **Response Quality**: Manual review of 5-10 responses
3. **Relevance**: Does tone match customer sentiment?
4. **Length Compliance**: Do responses respect max_sentences?

---

## Known Behaviors

- **Max sentences constraint**: Good LLMs (Claude, GPT-4) respect this ~95% of the time
- **Ollama/Mistral**: May not respect sentence limits as strictly. If you see 4+ sentences on "max_sentences=2", adjust your LLM or add examples
- **Tone directive compliance**: More reliable than sentence counting

---

## If Tests Fail

### Problem: Responses still too long

**Solution**: SentimentToneSignature might be outputting "4" instead of "2". Check:

1. Sentiment scores being passed correctly
2. LLM model capability (try Claude or GPT-4 if using Ollama)

### Problem: Tone doesn't match sentiment

**Solution**: ToneAwareResponseSignature might ignore the tone_directive. Try:

1. Make tone_directive more explicit in the description
2. Add examples in the signature
3. Test with a more capable LLM

### Problem: No `🎯 TONE ANALYSIS` logs

**Solution**: Logger level might be above DEBUG. Check main.py:

```python
'root': {
    'level': 'DEBUG',  # Should be DEBUG, not INFO
    ...
}
```

---

## Future Enhancements

Once this works:

1. **Add logging for tone decisions**: See what SentimentToneAnalyzer chose
2. **Add metrics collection**: Track response lengths by sentiment
3. **Train an optimizer**: Fine-tune the tone_directive → response mapping
4. **Add examples**: Provide few-shot examples in the signatures

---

## Command to Run Tests

```bash
cd /home/riju279/Downloads/demo/example

# Run conversation simulator
python tests/conversation_simulator.py

# With debug output
DEBUG=1 python tests/conversation_simulator.py
```

Look for response lengths and tone appropriateness in the conversation output.
