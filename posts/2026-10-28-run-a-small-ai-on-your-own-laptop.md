---
title: Run a small AI on your own laptop
summary: Local AI in plain English — why it is free, private, and easier to start than you would think.
tags: local-ai, beginners
---

Small AI models now run comfortably on an ordinary laptop. This week's topic:
what "local AI" means, why it is worth trying, and how to get one running
before your coffee cools.

## The topic in one sentence

*Local AI* means the model lives on your machine — you type, it answers, and
nothing leaves your laptop.

## Why it matters to you

- **Privacy.** Your words stay on your device. Nothing is sent to a server.
- **Cost.** The good open models are free, and your electricity bill will
  not notice.
- **Off-line.** Wi-Fi down? The model does not care. It runs anyway.
- **Patience.** No queues, no rate limits, no "you have used your free
  messages today."

## Try it yourself (step by step)

Pick the smallest path first. On most computers this takes about five
minutes:

1. Install a model runner — **Ollama** and **LM Studio** are the friendlier
   options for beginners.
2. Download one small model. On Ollama, that is one command:

```bash
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

3. Say hello. Ask it to summarize a paragraph you are reading. Ask it to
   rewrite your refund email in a firmer tone.

> Start small on purpose. A 3B-parameter model answers fast and teaches you
> what local AI feels like. You can always graduate to bigger models later —
> you will know exactly when, because the small one will start to feel slow.

## One friendly note

Local models are a little bland and a little clumsy. That is not failure —
that is what "runs on my laptop, in private" costs. Treat your local model
as a polite second opinion, not an oracle.

Next week's scheduled topic is already staged in `posts/` — see the
[next week page](../next.html) for how scheduling works.
