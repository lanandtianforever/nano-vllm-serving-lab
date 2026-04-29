# Interview Notes

## One-sentence project summary

I first built a local black-box serving baseline with LM Studio / MLX, then moved into a white-box scheduler lab to study prefill/decode trade-offs, tail latency, and goodput.

## Why not over-invest in local deployment

Because the local baseline is only a measurement scaffold.
The main signal comes from scheduler design, workload construction, metric definition, and experiment analysis.
