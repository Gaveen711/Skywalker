# Foundation architecture

Milestone 1 establishes a minimal `src/` package. `core.config` owns local
application paths; `core.logging` configures file logging. Milestone 2 adds a
Qt Widgets presentation layer. Milestone 3 defines `AIProvider` in the domain
and implements `OllamaProvider` as an HTTP adapter. The UI discovers models and
runs inference in `QThread` workers so network calls do not block rendering.
Milestone 4 stores conversation messages in SQLite through `ConversationStore`.
Each write is transactional, connections are closed after use, and message rows
are deleted with their parent conversation. The standard-library SQLite driver
avoids an additional native dependency on Windows ARM64. The same repository
provides explicit memory save/list/delete operations; its management UI is a
later feature. Storage capacity
comes from the operating system; unavailable metrics are labeled clearly.

Application state defaults to the operating system's per-user data location
and can be redirected with `SKYWALKER_DATA_DIR`. Logs and future model/database
files are outside the source tree by default. Conversations, credentials, and
prompt contents must not be written to source files or logged.

Future infrastructure integrations should be introduced behind domain or
application interfaces. Dependency and Windows ARM64 compatibility checks are
required before those packages are selected.
