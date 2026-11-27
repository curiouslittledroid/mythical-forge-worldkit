---
id: topic_timeline
kind: TOPIC
title: Timeline
name_status: working
status: working
engine: false
---

# Timeline

**Summary:** The world's eras, in order. The `era:` frontmatter field of a note may name only one of
these, and the linter checks it.

```eras
order: [REPLACE, present]
```

## Questions

1. **What are the three to six big blocks of time?** An age before, the break, the aftermath, the
   present — in the world's own words.
2. **When did each end, and what ended it?** The dates do not need to be fine-grained, but the
   order does, because every region and every people will be described against it.
3. **Which era are the campaigns in?** Usually the last one, and its slug should be `present`
   so that notes written today can be dated without a decision each time.

`REPLACE` the order above with the world's era slugs (kebab-case), then use the same slugs in each
note's `era:` field.
