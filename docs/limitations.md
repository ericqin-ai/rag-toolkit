# Known limits

- This is a retrieval toolkit/workbench, not LLM answer generation or a production
  hosted RAG service. Authentication, authorization, quotas and tenant persistence
  are not implemented; bind development services to localhost.
- Web sessions and the API have separate, in-memory indexes. Restart loses chunks,
  BM25 state and UI history. One API worker is required for consistent shared state.
  Existing remote vectors alone do not restore the local pipeline.
- Pipeline operations are not thread-safe on their own; the service serializes
  access. Remote Elasticsearch writes are not transactions. Session/rebuild indexes
  use isolated names; abandoned remote indexes need an external lifecycle policy.
- FAISS is exact cosine search and currently rebuilds on updates. Stable tie handling
  retrieves all candidates before truncation; target small/medium corpora.
- Splitting is character-based. PDF loading and semantic splitting are abstract
  extension points, not completed parsers. BM25 tokenizer settings do not change
  a real embedding model's tokenizer.
- Stage timings are measured query operations, not a hardware benchmark. BM25 and
  Dense are independent sources, currently executed sequentially. Avg/P95 across
  a few evaluation queries should not be interpreted as stable throughput figures.
- HashEmbedder/TokenOverlapReranker are offline test/sanity implementations. No
  real-model/public-dataset benchmark is published. Live real-model and external
  Elasticsearch integration, Docker image build/startup and GPU execution remain
  unverified here.
- Diagnostic labels are rule-based clues, not causal findings. Empty relevance sets
  score zero under the existing binary evaluation contract. Document IDs are
  deduplicated for metrics; MRR depends on the returned candidate truncation.
- Application-owned exports/UI redact credentials. API internal-error logs omit raw
  provider exceptions and tracebacks. Third-party HTTP/debug loggers are outside
  this policy: do not enable verbose external logging with secrets in URLs, or put
  secrets into arbitrary query/document/model-name fields.
- Browser screenshots are static viewport captures, not a recorded GIF. Browser
  smoke checks do not replace AppTest or a full manual accessibility audit.

[Documentation index](index.md)
