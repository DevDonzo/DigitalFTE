---
type: email
gmail_message_id: 19bbda6461dddb7f
from: Salman Paracha <paracha.salman@gmail.com>
subject: Fwd: Lambda Durable Functions: 5 gotchas to watch out for
received: 2026-01-14T12:56:14.261470
priority: high
status: pending
---

## From
Salman Paracha <paracha.salman@gmail.com>

## Subject
Fwd: Lambda Durable Functions: 5 gotchas to watch out for

## Body
---------- Forwarded message ---------
From: Yan Cui <yan@theburningmonk.com>
Date: Wed, Jan 14, 2026, 2:00 a.m.
Subject: Lambda Durable Functions: 5 gotchas to watch out for
To: <paracha.salman@gmail.com>


by *Yan Cui*
*The Master Serverless newsletter is brought to you by*
Honeycomb's Canvas (their AI chat assistant) helps you identify and debug
problems in minutes, instead of hours of manual investigation.
Try for free today
<https://256eb279.click.convertkit-mail2.com/27u6dme5mohoh8l2xkpb3hgz5m744hghn7xrg/48hvh7umwz4g35hx/aHR0cHM6Ly9mYW5kZi5jby80amJmVW96>

Lambda Durable Functions is a powerful new feature, but its checkpoint +
replay model has a few gotchas.

Here are five to watch out for.
Non-deterministic code

The biggest gotcha is when the code is not deterministic. That is, it might
do something different during replay.

Remember, when a durable execution is replayed, the handler code is
executed from the start. So the code must behave exactly the same given the
same input.

If you use random numbers, or timestamps to make branching decisions. Then
during a replay, the code might do something different! This is why, you
should capture the branching decision in a step instead. So, during a
replay, the previous decision is retrieved from the checkpoint logs.
Side-effecting code outside step

You should avoid causing side effects (e.g. updating databases, calling
external APIs, sending emails) outside steps.

This is to avoid causing the same side effects again during a replay.
Mutate closure variables

Avoid mutating variables that are captured in the closure, inside a step.
Because these mutations will be skipped during a replay, leading to
non-deterministic behaviour.
Dynamic step names

Avoid dynamic names for durable operations.

During replay, you get a different step name to the original invocation, so
the system won't be able to fetch the stored result from the checkpoint.
Child context results > 256kb are reconstructed during replay

You are working with child contexts whenever you use the
"runInChildContext", "parallel" or "map" operations. If a child context’s
result is greater than 256kb, then it’s not stored directly. During a
replay, its result is instead reconstructed by executing the context's
operations again.

This is mentioned in small print in the official documentation
<https://256eb279.click.convertkit-mail2.com/27u6dme5mohoh8l2xkpb3hgz5m744hghn7xrg/m2h7h6u32kde4gtm/aHR0cHM6Ly9kb2NzLmF3cy5hbWF6b24uY29tL2xhbWJkYS9sYXRlc3QvZGcvZHVyYWJsZS1leGVjdXRpb24tc2RrLmh0bWw=>
.

Take the following code as example:

If its result is less than 256kb, then it's stored in the database. On
replay, the result is fetched and the whole child context is skipped.

However, if the result is bigger than 256kb, then it's not saved. On
replay, the child context, and therefore this block of code, will be
executed again.

The previous durable operations ("step-1" and "step-2") will be skipped.
But any non-durable code will be executed again.

This interplays with the previous gotchas. For example, during a replay,
side-effecting actions outside of a step might be executed again if the
encompassing child context is re-evaluated.

​

Ok, that's five gotchas of working with Lambda Durable Functions.

Personally, I'm very excited about Durable Functions and it's something
that we're covering in the latest Production-Ready Serverless
<https://256eb279.click.convertkit-mail2.com/27u6dme5mohoh8l2xkpb3hgz5m744hghn7xrg/dphehmuedzl5pofm/aHR0cHM6Ly9wcm9kdWN0aW9ucmVhZHlzZXJ2ZXJsZXNzLmNvbS8_dXRtX2NhbXBhaWduPWxhbWJkYS1kdXJhYmxlLWZ1bmN0aW9ucyZ1dG1fc291cmNlPW5ld3NsZXR0ZXI=>
workshop.

In week 3 of the workshop, you will implement the same order processing
workflow using an event-driven approach, vs. Step Functions, vs. using
Durable Functions. So we can discuss the pros & cons of each approach.

It's still not too late to join us. Registration closes this Sunday, 18th
January.
------------------------------

*Whenever you're ready, here are 3 ways I can help you:*

   1.

   ​Production-Ready Serverless​
   <https://256eb279.click.convertkit-mail2.com/27u6dme5mohoh8l2xkpb3hgz5m744hghn7xrg/vqh3hmuom2zg6ksg/aHR0cHM6Ly9saW5rcy5wYWxsYWRpby5kZXYvZW5yaWNoLzg1MjEzNjQ5Mj9maWVsZF9pZD1uZXh0X29mZmVyJmZpZWxkX3ZhbHVlPXByc2xzJnJlZGlyZWN0PWh0dHBzJTNBJTJGJTJGcHJvZHVjdGlvbnJlYWR5c2VydmVybGVzcy5jb20lMkYlM0Z1dG1fY2FtcGFpZ24lM0QzLXdheXMtSS1jYW4taGVscCUyNnV0bV9zb3VyY2UlM0RuZXdzbGV0dGVyJTI2dXRtX2NvbnRlbnQlM0R0ZXh0LWxpbms=>:
   Join 20+ AWS Heroes & Community Builders and 1000+ other students in
   levelling up your serverless game. You can also get *15% OFF *as a
   newsletter subscriber with the code *LEVELUP15*.
   2.

   I help clients launch their product ideas, improve their development
   processes and upskill their teams. If you want to work together,
then let's get
   in touch
   <https://256eb279.click.convertkit-mail2.com/27u6d

## Actions
- [ ] Reply
- [ ] Forward
- [ ] Archive
