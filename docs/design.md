

`proxy` – main entrypoint
`meta` – main handler
`logic` – stateless service which get query and context and return operations need to be done, but doesn't execute them

User request goes to `proxy`. It decides which `meta` servers will handle this session. Factors for this:
- different message types e.g. suggest and text queries can be handled by different `meta` backends
- actual flags
- requested versions (if user has such permissions)


`meta` shared info about user, bot, session contexts and pass context it to `logic`
`meta` backend can query different `logic` servers due to flags and other configurations


User has session with bot.

Contexts:
- `user` User information stored in for bot
- `bot` Global bot settings like api keys and other
- `session` User session info
- `rule` Rule in conditions can set local context variables, which can be applyed to session variables if rule will be evaluated
