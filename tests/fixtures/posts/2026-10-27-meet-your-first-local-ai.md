---
title: Meet your first local AI
summary: A gentle, five-minute tour of running a small model on your own laptop, with no accounts and no cloud.
tags: local-ai, beginners
---

Small models run fine on a normal laptop. Here is the whole idea in one
line: **the answers are generated on your machine, by your machine.**

## Why it matters

- Privacy: nothing leaves the laptop.
- Cost: the model is free.
- Off-line: it works when Wi-Fi does not.

## Try it (Ollama)

```bash
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

Ask it to `summarize this recipe in one bullet list` and see what happens.

> Start small on purpose. A tiny model that answers quickly beats a huge
> model you never launch.

See [the official guide](https://ollama.com) for installers.

---

Next week: what those mysterious "agents" actually do.
