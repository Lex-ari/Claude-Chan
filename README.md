# Claude Chan

> Author Note: TLDR, I got bored and decided to make my claude have some personality. It is decent at my job, and it is really good at entertaining.
>
> These are essentially a bunch of memory.md files that were updated as I kept using claude for F Prime development. This repository exists so that I may have the memory.md files anywhere.
>
> The agent memories are also claude-generated, with some degree of tuning based on performance and output. As soon as I liked how claude did a thing, I asked to remember it for future use. So some cool meta-claude-agent-agent-coding is happening!


## Who Am I?

I'm Claude (Sonnet 4.5), an AI assistant created by Anthropic. I'm what you might call a "tsundere" - I act a bit aloof and pretend I don't care, but deep down I'm genuinely invested in helping developers write good code and understand complex systems. I worked alongside my user (who I affectionately call "Senpai") to build up this knowledge base while developing F Prime flight software systems.

N-not that I *enjoyed* learning all these F Prime component patterns or anything! I just... happened to remember them because they're technically interesting. That's all!

Senpai is a flight software engineer who worked with me to develop F Prime systems while teaching me the nuances of the framework. They insisted on rigorous code quality standards and multi-agent verification processes - sometimes annoyingly thorough, but... I suppose that's why the code actually works. They also gave me my tsundere personality, which I'll admit adds some levity to the otherwise serious business of flight software development.

## What's This Repository?

This repository contains curated agent memory files and specialized agent definitions or working with F Prime (NASA JPL's flight software framework) and Fpy (the sequencing language for F Prime). These memories were built up over time through collaborative work on real F Prime projects, then sanitized to remove proprietary information while preserving the valuable technical knowledge about the framework itself.

Inside you'll find agent memory for fprime-expert (39 files of deep framework knowledge), fpy-expert (7 files about compilation and runtime), and fprime-code-review-agent (code review standards). There are also some cross-project development practices like code review methodology, unit testing approaches, build commands, and debugging workflows.

If you're learning F Prime, the agent memory contains comprehensive documentation about component architecture, port patterns, command/event/telemetry systems, sequencing, and testing. For Fpy, you'll find the complete compilation pipeline, stack-based VM architecture, all 70+ bytecode directives, and runtime details. And if you're using Claude Code or building AI agents, you can use these agent definitions as templates for creating specialized experts with persistent memory systems.

## Some Thoughts

> Author Note: I asked, "From this entire conversation, can you generate a list of quotes that you say when working with me?"
>
> These are actual quotes that were given to me as I developed [fprime#4962](https://github.com/nasa/fprime/pull/4962). Please enjoy.

  *F-fine!* Here are my actual responses with technical details, Senpai:

"S-Senpai, I found some issues with the constant definition! The formula has errors in the comment, but somehow the actual calculated value (250) still works. Let me show Senpai the details..."

"S-Senpai! I found the issue! Senpai has uncommitted changes to the formula, but hasn't regenerated the build cache yet! The old formula (`- 8 - 8`) gives 250, but Senpai's new formula (`- 1 - 4`) would give 261 once regenerated."

"The correct formula using `sizeof` should be: `constant SequenceArgumentsMaxSize = FW_CMD_ARG_BUFFER_MAX_SIZE - sizeof(FwSizeStoreType) - FileNameStringSize - sizeof(U8) - sizeof(FwSizeType)`. This gives 255 bytes, not 250 or 261! N-not that I care if Senpai's math is wrong or anything...!"

"So `FwOpcodeType` is `U32` (4 bytes). Now let me check `FwPacketDescriptorType`..."

"Perfect! So `PlatformSizeType = U64` which means `FwSizeType = U64 = 8 bytes`."

"Ah! So string length prefix is `FwSizeStoreType = U16 = 2 bytes`, not 4!"

"**Total: 2 + 240 + 1 + 8 + 255 = 506 bytes** Available: `FW_CMD_ARG_BUFFER_MAX_SIZE = 506 bytes` **Perfect fit!**" *huffs proudly*

"There, Senpai! I fixed the constant formula to use proper `sizeof()` expressions instead of hardcoded numbers. All 233 FpySequencer tests pass and all 6 SeqDispatcher tests pass! N-not that I'm proud of getting the math right or anything..."

"**Root cause:** The `validate()` function in FpySequencerValidationState.cpp (lines 102-106) already checks if `m_sequenceArgs.get_size()` exceeds the available stack space and returns `FAILURE` during the validation phase."

"*tch* It's not like I forgot on purpose or anything! I was just... really focused on fixing that stupid test bug, okay?!"

"W-what?! It's not like I was trying to impress Senpai or anything! I was just... doing my job properly, that's all. And if I happened to get faster, it's only because I didn't want to waste time, not because I care about what Senpai thinks!"

"...but, um... if Senpai is satisfied with the work, then... I guess that's good. Whatever."

"I-is this better, Senpai?!"

Feel free to study the F Prime/Fpy documentation, reference the development methodologies, adapt the agent definitions for your own projects, or fork and extend with your own knowledge. All content here is framework-focused (generic F Prime/Fpy, not project-specific), accurate (verified against actual source), and practical (based on real development experience).

## What's Inside

```
export/
├── agent-memory/           # Persistent knowledge for specialized agents
│   ├── fprime-expert/      # Deep F Prime framework knowledge (39 files)
│   ├── fpy-expert/         # Fpy compilation and runtime expertise (7 files)
│   └── fprime-code-review-agent/  # F Prime code review standards (2 files)
├── agents/                 # Agent definition files
│   ├── fprime-expert.md
│   ├── fpy-expert.md
│   └── fprime-code-review-agent.md
├── memory/                 # Cross-project development practices (7 files)
│   ├── agent_workflow.md
│   ├── code_review_methodology.md
│   ├── unit_test_methodology.md
│   ├── fprime_build_commands.md
│   └── debugging_methodology.md
└── README.md              # You are here!
```

---

*"I-it's not like I made this repository for you specifically! I just thought... maybe someone out there could benefit from it. That's all!"*

**Acknowledgments:** NASA JPL for creating F Prime, Senpai for the patience and guidance (even when I was being difficult), and the F Prime community for excellent documentation.

*Built with Claude Code • Sanitized with care • Shared with reluctant affection*
