---
title: What is MCP, in plain English
summary: Model Context Protocol sounds like buzzword soup. It is really just one idea — a standard plug for AI tools — and it clicks once you see it.
tags: agents, mcp, beginners
---

Last week we ran a small AI on a laptop. This week we zoom out: how does
your AI *do things* — read a file, check a calendar, search the web?
The answer everyone settled on in 2025 is a plug standard called MCP.

## The topic in one sentence

**MCP (Model Context Protocol)** is a shared plug format that lets any AI
tool talk to any capability — like USB, but for AI.

## Why it matters to you

- One AI tool can gain new abilities without being rebuilt.
- One small server program can serve *many* different AI tools.
- You stop gluing custom integrations together for every combination.

## Try it yourself (step by step)

1. Read the friendly official explainer once, slowly:
   [modelcontextprotocol.io](https://modelcontextprotocol.io). It is shorter
   than you fear.
2. Look at a tiny MCP server — for example one that exposes your notes
   folder. The code is mostly *a list of functions with names and
   descriptions*.
3. Picture your own daily loops. Which two tools would you wire together
   first?

```text
AI assistant  <->  MCP  <->  your notes
                            your calendar
                            your file search
```

> Middle of the road: you do not need to write an MCP server this week.
> Understanding *what the plug is for* is the skill that pays next month,
> when you pick tools and instantly know which ones cooperate.

## One friendly note

When someone says "agent" with a serious face, they usually mean: a model,
looping, calling tools through things like MCP until the job is done.
Drama optional.
