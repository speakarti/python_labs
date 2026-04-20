Now, here is the full analysis of your AI workloads:
# Contracts AI IQT — Complete AI Workload Analysis

## System Overview

**contracts-ai-iqt** is a **healthcare contract intelligence platform** — a document understanding pipeline that ingests PDF contracts, extracts entities, answers natural language queries, and generates SQL reports. It is a **15-service microservices system** driven by AWS SQS message queues.

---

## Pipeline Architecture

```
PDF Upload → Preprocessing → BBox Generation → Text Extraction → Page Classification
                                                                         ↓
                                                                   Linearization
                                                                         ↓
                                                                     Chunking → OpenSearch (Vector DB)
                                                                         ↓
                                            Prompt Gen → LLM Inference ← Context Retrieval + Reranking
                                                                         ↓
                                                               QA System / Text-to-SQL / Evaluation
```

---

## All 15 Workloads

### 1. Preprocessing Service
| | |
|---|---|
| **Entry point** | `iqt_main_preprocessing.py` |
| **Dockerfile** | `Dockerfile-iqt-preprocessing` |
| **Language/Framework** | Python 3.10, PyTorch 2.6.0 |
| **AI Models** | Tesseract OCR (pytesseract), AWS Textract |
| **Key Libraries** | pdf2image, PyMuPDF 1.24.4, pytesseract, mistralai 1.6.0 |
| **External Services** | AWS S3, AWS Textract, Mistral AI API |
| **GPU** | None (CPU only) |
| **Pattern** | Batch SQS processing |

**What it does:** Converts PDFs to images, runs OCR, normalizes text via fuzzy matching.

---

### 2. BBox Generation (Layout Detection)
| | |
|---|---|
| **Entry point** | `iqt_main_bbox_generation.py` |
| **Dockerfile** | `Dockerfile-iqt-bbox-generation` |
| **Language/Framework** | Python 3.10, detectron2 |
| **AI Models** | **DonutDet** — custom fine-tuned DETR-based object detector (ViT backbone) |
| **Key Libraries** | transformers 4.53.0, timm 0.9.16, accelerate 0.33.0, PyPDFium2 |
| **External Services** | AWS S3 (model weights + documents), AWS RDS |
| **GPU** | CUDA required |
| **Pattern** | Single-pass layout detection per PDF page |

**What it does:** Detects bounding boxes for tables, headers, paragraphs using a custom DETR model fine-tuned on healthcare contracts.

**Model basis:** DETR (DEtection TRansformer) — treats object detection as a set prediction problem. ViT encodes visual features; transformer decoder predicts bounding boxes. Fine-tuned from a Donut/DETR checkpoint on proprietary contract layout data.

---

### 3. Text Generation (Textract)
| | |
|---|---|
| **Entry point** | `iqt_main_text_generation.py` |
| **Dockerfile** | `Dockerfile-iqt-text-generation` |
| **Language/Framework** | Python 3.10 |
| **AI Models** | AWS Textract (managed, cloud-based) |
| **Key Libraries** | amazon-textract-caller 0.2.3, amazon-textract-textractor 1.7.10, PyPDFium2 |
| **External Services** | AWS Textract API, AWS S3, AWS RDS |
| **GPU** | None |
| **Pattern** | Async API calls to AWS Textract |

**What it does:** Extracts text from PDF regions using AWS Textract, preserving layout structure.

---

### 4. Page Classification
| | |
|---|---|
| **Entry point** | `iqt_main_page_classification.py` |
| **Dockerfile** | `Dockerfile-iqt-page-classification` |
| **Language/Framework** | Python 3.10, HuggingFace Transformers |
| **AI Models** | **LayoutLMv2ForSequenceClassification** — client-specific fine-tuned |
| **Key Libraries** | transformers 4.48.0, safetensors, PyTorch CUDA |
| **External Services** | AWS S3 (model weights per client), AWS RDS |
| **GPU** | CUDA (batch DataLoader inference) |
| **Pattern** | Batch page classification |

**What it does:** Classifies each document page into categories (e.g., rates table, definitions, amendments) using a fine-tuned LayoutLMv2 per client.

**Model basis:** LayoutLMv2 — multimodal pre-trained model combining text tokens + 2D positional embeddings (bounding box coordinates) + visual features from the scanned page image. Pre-trained on IIT-CDIP dataset with masked visual-language modeling. Fine-tuned here for sequence classification (page type) on client-specific contract pages.

---

### 5. Linearization Service
| | |
|---|---|
| **Entry point** | `iqt_main_linearize.py` |
| **Dockerfile** | `Dockerfile-iqt-linearizer` |
| **Language/Framework** | Python 3.10, Pandas, OpenPyXL |
| **AI Models** | None (rule-based) |
| **External Services** | AWS S3, AWS RDS |
| **GPU** | None |
| **Pattern** | Sequential processing |

**What it does:** Converts BBox + text data into reading-order linear document representation preserving spatial relationships.

---

### 6. Chunking Service ⭐ GPU Workload
| | |
|---|---|
| **Entry point** | `iqt_main_chunking.py` |
| **Dockerfile** | `Dockerfile-iqt-chunking` (CUDA 12.6 multi-stage) |
| **Language/Framework** | Python 3.10, uv package manager, PyTorch 2.6.0+cu124 |
| **AI Models** | HuggingFace AutoModel embedding model (local), FlagEmbedding 1.2.11 |
| **Key Libraries** | bitsandbytes ≥0.45.0, transformers 4.48.0, accelerate, peft 0.12.0, sentence-transformers, opensearch-py 2.5.0 |
| **External Services** | AWS S3, AWS SQS, OpenSearch, AWS RDS |
| **GPU** | CUDA 12.6, NVIDIA cuDNN, 4-bit quantization |
| **Pattern** | Batch embedding + real-time vector indexing |

**What it does:** Splits linearized documents into semantic chunks, generates dense embeddings, indexes them in OpenSearch for hybrid retrieval.

**Model basis:** Dense retrieval embedding model (likely BGE or similar) using a transformer encoder with average pooling + L2 normalization. Uses 4-bit NF4 quantization via bitsandbytes to reduce GPU memory ~4x. LoRA support via PEFT for fine-tuning if needed.

---

### 7. Context Retrieval / RAG Service ⭐
| | |
|---|---|
| **Entry point** | `iqt_main_context_retrieval.py` |
| **Language/Framework** | Python 3.10, HuggingFace Transformers |
| **AI Models** | AutoModel embedding (same as chunking), NLTK for query processing |
| **Key Libraries** | transformers 4.48.0, sentence-transformers 3.0.1, FlagEmbedding 1.2.11, opensearch-py, rapidfuzz 3.9.6 |
| **External Services** | OpenSearch (vector search), AWS S3, AWS RDS |
| **GPU** | Optional (CUDA if available) |
| **Pattern** | Query-time retrieval with batch embedding |

**What it does:** Handles RAG retrieval — embeds queries, runs hybrid search (keyword + semantic) on OpenSearch, extends chunks by window, returns top-K candidates.

---

### 8. Context Reranking
| | |
|---|---|
| **Language/Framework** | Python 3.10 |
| **AI Models** | **mixedbread-ai/mxbai-rerank-large-v1** (CrossEncoder), **BAAI/bge-reranker-v2-m3** (FlagReranker) |
| **Key Libraries** | sentence-transformers 3.0.1, FlagEmbedding 1.2.11, mistralai (tokenizer) |
| **External Services** | HuggingFace Hub (model loading), AWS S3 |
| **GPU** | CUDA, FP16 inference |
| **Pattern** | Listwise reranking post-retrieval |

**What it does:** Re-scores retrieved chunks against the query using cross-encoder (not bi-encoder) architecture. Token-budget aware — trims context to fit LLM prompt window.

**Model basis:**
- **mxbai-rerank-large-v1**: Cross-encoder BERT-style model. Takes (query, passage) pair as input, outputs single relevance score. Cannot be pre-computed — runs at query time. ~350M params.
- **bge-reranker-v2-m3**: FlagEmbedding cross-encoder, multilingual, with stronger performance on domain-specific text.

---

### 9. Prompt Generation
| | |
|---|---|
| **Entry point** | `iqt_main_prompt_gen.py` |
| **Dockerfile** | `Dockerfile-iqt-prompt-gen` |
| **Language/Framework** | Python 3.10, Pydantic, YAML |
| **AI Models** | None (template rendering) |
| **External Services** | AWS S3, AWS RDS, AWS SQS |
| **GPU** | None |

**What it does:** Assembles final LLM prompts from retrieved context + entity schema + templates. Generates JSON schemas for constrained generation.

---

### 10. LLM Inference Service ⭐⭐ PRIMARY AI WORKLOAD
| | |
|---|---|
| **Entry point** | `iqt_main_inference.py` |
| **Dockerfiles** | `Dockerfile-iqt-inference` (CPU), `Dockerfile-iqt-inference-gpu` (CUDA 12.1) |
| **Language/Framework** | Python 3.10, transformers 4.48.0, outlines 0.0.46, langchain 0.1.13 |

**LLM Backends (multi-provider):**

| Provider | Model | Library | Config |
|---|---|---|---|
| **OpenAI** | GPT-4o | openai 1.76.0 | temp=0.5, max_tokens=2000, top_p=0.9 |
| **AWS Bedrock** | Meta Llama 3.1 70B Instruct | boto3 | via `meta.llama3-1-70b-instruct-v1:0` |
| **AWS Bedrock** | Anthropic Claude (v2) | boto3 | via `bedrock-2023-05-31` |
| **AWS Bedrock** | Mistral, DeepSeek | boto3 | model family handlers |
| **Google GenAI** | Gemini 2.0-flash | google-genai 1.12.1 | temp=1.0, max_tokens=2000 |
| **HorizonHub** | Llama 3.1 70B | internal SDK | temp=0.01, max_tokens=2000 |
| **SLIP** | meta-llama/Meta-Llama-3.1-70B-Instruct | internal gateway | constrained JSON generation |
| **Local HF** | Configurable | transformers | 4-bit quantization |

**Key Features:**
- **Constrained generation** via `outlines` — forces LLM output to conform to JSON schema (critical for entity extraction reliability)
- **4-bit quantization** via `BitsAndBytesConfig` for local model memory efficiency
- **Multi-GPU** via `accelerate`
- **Entity extraction** with hierarchical parent chains

**GPU Requirements:** CUDA 12.1, multi-GPU via accelerate, 4-bit NF4 quantization

**Model basis (Llama 3.1 70B):** Meta's 70B parameter autoregressive transformer. Trained on 15T tokens with grouped-query attention (GQA), RoPE positional embeddings, SwiGLU activations, RMSNorm. At 4-bit quantization, fits in ~35GB GPU memory (e.g., 2× A10G or 1× A100 80GB). Used here for complex entity extraction from healthcare contract text.

---

### 11. QA System (IQT_QA) ⭐
| | |
|---|---|
| **Entry point** | `src/qa/iqt_qa.py` |
| **Dockerfile** | `src/qa/Dockerfile` |
| **Framework** | xiqt (HorizonLabs internal framework) |
| **LLM** | **anthropic/claude-3-7-sonnet** via HorizonHub (temp=0.0, max_tokens=2000) |
| **Embedding** | HorizonHub embeddings (cached) |
| **Rerankers** | mxbai-rerank-large-v1, bge-reranker-v2-m3 (configurable per use-case) |
| **Key Libraries** | transformers 4.48.0, sentence-transformers 3.0.1, opensearch-py 2.5.0 |
| **External Services** | HorizonHub API, OpenSearch (multi-index), AWS S3, AWS RDS |
| **GPU** | Optional |
| **Pattern** | Streaming RAG — retrieval + generation |

**Use-cases:** CONTRAXX, PROVIDER_MANUALS, STATE_AGREEMENTS, DEFAULT (each with own OpenSearch index, reranker config, top_k)

---

### 12. Text-to-SQL Service
| | |
|---|---|
| **Entry point** | `iqt_main_text_to_sql.py` |
| **Dockerfile** | `Dockerfile-iqt-text-to-sql` |
| **LLMs** | GPT-4o (OpenAI), Gemini 2.0-flash (Google) |
| **Key Libraries** | openai 1.76.0, google-genai 1.12.1 |
| **External Services** | OpenAI API / Google GenAI API, AWS SQS, AWS S3, AWS RDS, **Snowflake** |
| **GPU** | None |
| **Pattern** | Few-shot prompted SQL generation → Snowflake execution |

**What it does:** Converts NL questions to SQL for COST_OF_CARE use case, executes on Snowflake, stores results.

---

### 13. Evaluation Service
| | |
|---|---|
| **Entry point** | `iqt_main_evaluation.py` |
| **LLM** | Claude models via HorizonHub (LLM-as-judge) |
| **Metrics** | is_equivalent, completeness_score, correctness_score |
| **External Services** | HorizonHub API, AWS S3, AWS RDS |
| **GPU** | None |
| **Pattern** | Batch evaluation with LLM judge |

---

### 14. Cron / Ingestion Jobs
- **Dockerfiles:** `Dockerfile-iqt-ingestion-service`, `Dockerfile-iqt-provider-manual-ingestion`, `Dockerfile-iqt-update-rds`
- **Tech:** boto3, pandas, fastparquet
- **Services:** AWS S3, AWS RDS, AWS SQS, Snowflake
- **GPU:** None
- Scheduled ingestion from Contraxx source system

---

### 15. Flask API Endpoint
| | |
|---|---|
| **Entry point** | `app_endpoint/ds_endpoint.py` |
| **Dockerfile** | `Dockerfile-iqt-flask` |
| **Framework** | Flask 3.0.3, Flask-Cors 5.0.0 |
| **AI** | Paraphrasing service (Parrot class), document highlighting |
| **External Services** | All downstream services via SQS, AWS S3, AWS RDS |
| **GPU** | None |

---

## Complete Model Inventory

| Model | Type | Size | Provider | How Used |
|---|---|---|---|---|
| GPT-4o | LLM | ~200B | OpenAI API | Entity extraction, Text-to-SQL |
| Claude 3.7 Sonnet | LLM | ~70B | AWS Bedrock / HorizonHub | QA, Evaluation (LLM-judge) |
| Llama 3.1 70B Instruct | LLM | 70B | AWS Bedrock / SLIP / Local | Entity extraction, primary inference |
| Gemini 2.0-flash | LLM | Unknown | Google GenAI | Text-to-SQL, QA |
| DonutDet | Vision (DETR) | Custom | Local (S3 weights) | Bounding box / layout detection |
| LayoutLMv2 | Document Understanding | ~200M | Local (S3, fine-tuned per client) | Page classification |
| BGE/HF Embedding Model | Embedding | ~110-560M | Local / HorizonHub | Dense retrieval |
| mxbai-rerank-large-v1 | Cross-encoder Reranker | ~350M | HuggingFace Hub | Context reranking |
| BAAI/bge-reranker-v2-m3 | Cross-encoder Reranker | ~568M | HuggingFace Hub | Context reranking |
| AWS Textract | OCR | Managed | AWS | Text extraction from PDFs |
| Tesseract | OCR | Managed | System | Fallback OCR |

---

## External Services & APIs

| Service | Purpose | Auth |
|---|---|---|
| AWS S3 | Document storage, model weights, configs, outputs | IAM |
| AWS SQS | Inter-service message queuing (work distribution) | IAM |
| AWS RDS (PostgreSQL) | Metadata, status tracking, config table | IAM |
| AWS Textract | Cloud OCR | IAM |
| AWS Bedrock | LLM inference (Llama, Claude, Mistral) | IAM |
| OpenSearch | Vector DB for RAG (hybrid search) | VPC / IAM |
| HorizonHub | Internal LLM gateway (Claude, Llama) | Token |
| SLIP | Internal constrained-gen LLM service | Token |
| OpenAI API | GPT-4o | API Key |
| Google GenAI | Gemini 2.0-flash | API Key / VertexAI |
| Snowflake | Data warehouse for SQL queries | Username/Pass |
| HuggingFace Hub | Reranker model downloads | Token |
| Protegrity | Data encryption | Internal |

---

## How These Models Were Developed — Educational Deep Dive

### Foundation: The Transformer Architecture
All modern AI models in this repo are built on the **Transformer** (Vaswani et al., 2017). The key innovation is **self-attention**: every token attends to every other token in the sequence, capturing long-range dependencies that RNNs failed at.

```
Input tokens → Embeddings → N× (Self-Attention + FFN) → Output
```

### GPT-4o / Llama 3.1 — Decoder-Only LLMs
**Training basis:**
1. **Pre-training**: Next-token prediction on trillions of tokens (Common Crawl, books, code, papers). Loss = cross-entropy on predicted vs. actual next token. This gives the model language understanding and world knowledge.
2. **Supervised Fine-Tuning (SFT)**: Trained on human-written instruction-response pairs (e.g., "Extract the rates from this contract → [answer]").
3. **RLHF / DPO**: Trained with human preference data to be helpful, harmless, and honest. A reward model scores outputs; PPO or DPO adjusts weights to maximize reward.

**Key architectural choices in Llama 3.1:**
- **Grouped Query Attention (GQA)**: Multiple query heads share key/value heads → reduces KV cache memory at inference
- **RoPE (Rotary Position Embeddings)**: Better extrapolation to longer sequences
- **SwiGLU activations**: Better than ReLU empirically
- **RMSNorm** instead of LayerNorm: Faster, no mean-centering

**Why used here:** 70B parameter scale gives strong reasoning for complex healthcare contract clauses. 4-bit quantization (NF4 via bitsandbytes) reduces memory to ~35GB, fitting on 2×A10G (48GB VRAM total).

### Claude 3.7 Sonnet — Constitutional AI
Similar decoder-only transformer but trained by Anthropic using **Constitutional AI (CAI)** — a set of principles guiding the RLHF/RLAIF stage. Better instruction following and lower hallucination rate, which is why it's used for the QA system where accuracy matters most.

### LayoutLMv2 — Document AI (Multimodal Pre-training)
**Training basis:** Pre-trained by Microsoft on **IIT-CDIP** (11M scanned document images). Three pre-training objectives:
1. Masked Visual-Language Modeling (MVLM) — predict masked text tokens using image + layout context
2. Text-Image Alignment — predict whether an image region matches its text
3. Text-Image Matching — binary: is this image paired with this text?

**Architecture:**
```
Text tokens + BBox coordinates → LayoutLM encoder (BERT-based)
                                              ↑
Document image regions → Visual encoder (ResNeXt-101) ──┘
```

**Fine-tuning here:** The per-client model takes the 512-class layout representation and trains a linear classification head on top — what page type is this (rates table, amendment, definitions, etc.)? Fine-tuned on labeled pages from each client's specific contract style.

### DonutDet — Custom DETR for Layout Detection
**Training basis:** DETR (DEtection TRansformer, Facebook 2020) reformulates object detection as direct set prediction:
- No NMS (Non-Maximum Suppression) post-processing
- Transformer decoder queries → directly predicts N bounding boxes
- Hungarian matching loss during training matches predictions to ground truth

**Architecture:**
```
Document page image → CNN/ViT backbone → Transformer encoder → Transformer decoder (N learned queries) → Bounding boxes + class labels
```

**DonutDet customization:** Fine-tuned on labeled contract page images with bounding boxes for specific layout elements (tables, section headers, fee schedules, signature blocks).

### Embedding Models (BGE, mxbai) — Dense Retrieval
**Training basis:**
- Pre-trained as BERT-style **masked language models** (predict masked tokens)
- Fine-tuned with **contrastive learning** (SimCSE, MNRL loss): pull together semantically similar sentence pairs, push apart dissimilar ones
- BGE uses BEIR benchmark + domain-specific data for robustness

**Architecture:**
```
Sentence → BERT encoder → [CLS] token → Average pool → L2 normalize → Dense vector (768-4096 dims)
```

**At query time:** Query and document vectors are compared via cosine similarity. The top-K nearest neighbors are the retrieved chunks.

### Cross-Encoder Rerankers (mxbai-rerank, bge-reranker)
**Why different from embeddings:**
- Bi-encoders (embeddings) encode query and doc *separately* — fast at retrieval but miss fine-grained interactions
- Cross-encoders concatenate `[query, document]` and score together — captures token-level interaction but cannot be pre-computed

**Training:** Fine-tuned on MS-MARCO relevance labels + domain data using binary cross-entropy loss (relevant=1, not relevant=0). Used as a second-stage reranker in this system.

---

## EKS Deployment Guide for Optimal GPU Utilization

### GPU Workload Classification

| Service | GPU Need | Instance Type | Strategy |
|---|---|---|---|
| **LLM Inference** (Llama 3.1 70B 4-bit) | 35-40GB VRAM | `p4d.24xlarge` (8×A100 80GB) or `g5.12xlarge` (4×A10G 24GB) | Multi-GPU with tensor parallelism |
| **Chunking** (embedding) | 4-8GB VRAM | `g4dn.xlarge` (T4 16GB) | Single GPU, batch embedding |
| **Page Classification** (LayoutLMv2) | 4-8GB VRAM | `g4dn.xlarge` | Single GPU, batch inference |
| **BBox Generation** (DonutDet) | 8-16GB VRAM | `g4dn.2xlarge` | Single GPU |
| **Context Reranking** | 4-8GB VRAM | `g4dn.xlarge` | Single GPU, FP16 |

### Node Group Strategy

```yaml
# EKS Node Groups
GPU Tier 1 - Large LLM Inference:
  instanceType: g5.12xlarge  # 4×A10G = 96GB VRAM
  minSize: 1
  maxSize: 10
  labels:
    workload: llm-inference
  taints:
    - key: nvidia.com/gpu
      value: "true"
      effect: NoSchedule

GPU Tier 2 - Small GPU (Embedding, Classification, Reranking):
  instanceType: g4dn.xlarge  # 1×T4 16GB
  minSize: 2
  maxSize: 20
  labels:
    workload: ml-inference-small

CPU Tier - Stateless Services:
  instanceType: m5.2xlarge
  minSize: 3
  maxSize: 30
  labels:
    workload: cpu-only
```

### Kubernetes Resource Requests

```yaml
# LLM Inference Deployment (Llama 3.1 70B @ 4-bit)
resources:
  requests:
    cpu: "8"
    memory: "32Gi"
    nvidia.com/gpu: "2"      # 2×A10G = 48GB for 35GB model
  limits:
    cpu: "16"
    memory: "64Gi"
    nvidia.com/gpu: "2"

# Chunking / Embedding
resources:
  requests:
    nvidia.com/gpu: "1"
    memory: "16Gi"
  limits:
    nvidia.com/gpu: "1"
    memory: "32Gi"

# Page Classification / BBox
resources:
  requests:
    nvidia.com/gpu: "1"
    memory: "8Gi"
  limits:
    nvidia.com/gpu: "1"
    memory: "16Gi"

# CPU-only services (preprocessing, linearization, prompt gen, flask)
resources:
  requests:
    cpu: "1"
    memory: "2Gi"
  limits:
    cpu: "4"
    memory: "8Gi"
```

### GPU Sharing — NVIDIA MPS / Time-Slicing

For small models (reranker, embedding, classification) that don't fill a GPU:

```yaml
# ConfigMap for NVIDIA Device Plugin - GPU Time-Slicing
apiVersion: v1
kind: ConfigMap
metadata:
  name: nvidia-device-plugin-config
data:
  config.yaml: |
    version: v1
    sharing:
      timeSlicing:
        resources:
        - name: nvidia.com/gpu
          replicas: 4   # Split 1 GPU across 4 pods (for g4dn.xlarge T4)
```

This lets 4 small-model pods (reranker, embedding, classification, BBox) share one T4 GPU, 4× better utilization vs. one pod per GPU.

### Horizontal Pod Autoscaler Based on SQS Queue Depth

Since all services are SQS-driven, scale on queue depth not CPU:

```yaml
# KEDA ScaledObject for LLM Inference
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: iqt-inference-scaler
spec:
  scaleTargetRef:
    name: iqt-inference-deployment
  minReplicaCount: 1
  maxReplicaCount: 8
  triggers:
  - type: aws-sqs-queue
    metadata:
      queueURL: https://sqs.us-east-1.amazonaws.com/xxx/iqt-inference-queue
      queueLength: "5"        # 1 pod per 5 messages in flight
      awsRegion: us-east-1
      identityOwner: operator  # Use IRSA
```

Use **KEDA** (Kubernetes Event-Driven Autoscaling) — scales GPU pods to zero when no SQS messages, saving cost.

### Model Loading Strategy — Avoid Cold Starts

The biggest GPU utilization killer is loading a 35GB model from S3 on every pod startup (~5-10 minutes):

```yaml
# Use EFS-backed persistent volumes for model cache
volumes:
- name: model-cache
  persistentVolumeClaim:
    claimName: efs-model-cache  # AWS EFS, mounted ReadOnlyMany

# Init container pre-warms model
initContainers:
- name: model-warmer
  image: aws-cli
  command: ["aws", "s3", "sync", "s3://models/llama-3.1-70b/", "/cache/llama/"]
  volumeMounts:
  - name: model-cache
    mountPath: /cache
```

**Alternative:** Use **Karpenter** with `consolidation: true` to keep GPU nodes warm (not scale to zero) during business hours but terminate at night.

### IRSA (IAM Roles for Service Accounts)

Each service needs scoped AWS permissions — avoid wide IAM roles:

```yaml
# Service Account with IRSA
apiVersion: v1
kind: ServiceAccount
metadata:
  name: iqt-inference-sa
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/iqt-inference-role

# IAM Role Policy - only what inference needs
{
  "Statement": [
    {"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::iqt-models/*"},
    {"Effect": "Allow", "Action": ["sqs:ReceiveMessage", "sqs:DeleteMessage"], "Resource": "arn:aws:sqs:::iqt-inference-queue"},
    {"Effect": "Allow", "Action": ["bedrock:InvokeModel"], "Resource": "*"},
    {"Effect": "Allow", "Action": ["rds-data:ExecuteStatement"], "Resource": "arn:aws:rds:::iqt-db"}
  ]
}
```

### Observability for GPU Utilization

```yaml
# NVIDIA DCGM Exporter for Prometheus
helm install dcgm-exporter nvidia/dcgm-exporter

# Key metrics to alert on:
# DCGM_FI_DEV_GPU_UTIL < 40%  → underutilized, consolidate pods
# DCGM_FI_DEV_FB_USED > 90%  → OOM risk, add memory limit
# DCGM_FI_DEV_SM_ACTIVE      → actual compute utilization
# DCGM_FI_DEV_MEM_COPY_UTIL  → memory bandwidth (embedding bottleneck)
```

### Recommended EKS Add-ons

| Add-on | Purpose |
|---|---|
| **NVIDIA Device Plugin** | Expose GPU resources to k8s |
| **NVIDIA DCGM Exporter** | GPU metrics for Prometheus/Grafana |
| **KEDA** | SQS-driven autoscaling |
| **Karpenter** | Node provisioning with GPU awareness |
| **AWS Load Balancer Controller** | ALB for Flask API |
| **External Secrets Operator** | Pull secrets from AWS Secrets Manager |
| **Fluent Bit** | Log shipping to CloudWatch |

### Cost Optimization Summary

| Strategy | Savings |
|---|---|
| Scale LLM pods to zero via KEDA when SQS empty | 60-80% GPU cost reduction (batch workload) |
| GPU time-slicing for small models (reranker, embedding) | 4× utilization on T4 instances |
| Spot instances for preprocessing/CPU services | 60-70% cost reduction |
| EFS model cache (avoid S3 download per pod) | Eliminates 5-10min cold start |
| Llama 3.1 70B at 4-bit quantization vs FP16 | 4× GPU memory reduction, 2× throughput |
| Use Bedrock (API) vs local Llama for low-volume | Eliminates GPU cost for tail traffic |




This is a deep question — let me give you a complete, opinionated answer structured as a learning roadmap + tool suite + EKS architecture, all grounded in what this specific project actually needs.






---

# TRAININIG PLAN - MLOps/DevOps Complete Roadmap for Contracts AI IQT

## The Core Problem First

Before tools — here's why this project has high GPU cost today:

| Root Cause | Symptom | Fix |
|---|---|---|
| No scale-to-zero | GPU nodes run 24/7 even with no work | KEDA + Karpenter |
| No GPU sharing | 1 small model = 1 full GPU | NVIDIA time-slicing / MPS |
| No model caching | 35GB model re-downloads on every pod start | EFS model cache |
| No batching | 1 request = 1 LLM call | Dynamic batching (vLLM) |
| No quantization tuning | FP16 where INT4 would suffice | bitsandbytes / AWQ / GPTQ |
| No right-sizing | Oversized instances for workload | Karpenter + resource profiling |
| No spot usage | On-demand everywhere | Spot for stateless GPU pods |
| No inference server | Raw HuggingFace inference (inefficient) | vLLM / TGI / Triton |

---

## Learning Roadmap — Ordered by Priority

### Phase 1: Foundations (Weeks 1–4)

**Learn these first — everything else builds on them.**

```
Linux + Bash scripting
  → Docker (build, layer caching, multi-stage builds)
    → Kubernetes fundamentals (pods, deployments, services, configmaps, PVC)
      → kubectl + Helm
        → AWS core (IAM, VPC, S3, EC2, SQS, RDS)
```

**Why this order:** You can't debug a broken EKS pod without understanding all four layers simultaneously.

**Resources:**
- Docker: official docs + `docker system df` / `docker buildx`
- K8s: `kubernetes.io/docs` + killer.sh CKA practice
- AWS: AWS Skill Builder (free) — Solutions Architect Associate level

---

### Phase 2: Container & K8s for ML (Weeks 5–8)

```
EKS cluster setup (eksctl / Terraform)
  → NVIDIA device plugin + GPU node groups
    → Helm chart authoring
      → Karpenter (node provisioning)
        → KEDA (event-driven autoscaling)
          → AWS Load Balancer Controller
            → External Secrets Operator
              → Fluent Bit → CloudWatch
```

**Key concept to internalize:** Kubernetes resource requests/limits are NOT suggestions — they drive the scheduler. A pod with `request: 1 GPU` on a node with time-slicing enabled behaves completely differently from one without it.

---

### Phase 3: ML-Specific Infrastructure (Weeks 9–14)

This is where MLOps diverges from pure DevOps:

```
Model serving frameworks:
  vLLM (LLM inference server) ← most important for this project
  NVIDIA Triton Inference Server (multi-framework)
  TorchServe (PyTorch models)
  BentoML (packaging + serving)

GPU optimization:
  NVIDIA MPS (Multi-Process Service) — true GPU sharing
  NVIDIA time-slicing — virtual GPU sharing
  TensorRT — model compilation for NVIDIA GPUs
  bitsandbytes — runtime quantization
  AWQ / GPTQ — offline weight quantization (better than bitsandbytes for deployment)
  Flash Attention 2 — memory-efficient attention

Experiment tracking:
  MLflow — tracking, model registry, artifact store
  Weights & Biases (W&B) — richer UI, sweeps
  DVC — data + model versioning (Git for data)

Pipeline orchestration:
  Apache Airflow — DAG-based pipeline orchestration
  Prefect — more Pythonic alternative to Airflow
  Kubeflow Pipelines — K8s-native ML pipelines
```

---

### Phase 4: Observability & Cost (Weeks 15–18)

```
Prometheus + Grafana (metrics)
  → NVIDIA DCGM Exporter (GPU metrics)
    → OpenTelemetry (distributed tracing)
      → Jaeger / Tempo (trace backends)
        → Loki (log aggregation)
          → AWS Cost Explorer + Kubecost (cost attribution)
            → Opencost (open-source cost)
```

---

### Phase 5: GitOps & Platform Engineering (Weeks 19–22)

```
Terraform (IaC for AWS)
  → Terragrunt (DRY Terraform)
    → ArgoCD (GitOps for K8s deployments)
      → GitHub Actions / GitLab CI (CI/CD pipelines)
        → Kaniko / ko (in-cluster container builds)
          → OPA / Kyverno (policy enforcement)
            → Vault / AWS Secrets Manager (secrets)
```

---

## Complete Tool Suite — By Category

### 1. Infrastructure as Code

| Tool | Purpose | Priority |
|---|---|---|
| **Terraform** | AWS resource provisioning (EKS, VPC, S3, RDS, SQS) | Must-have |
| **Terragrunt** | DRY Terraform — manage dev/uat/prod without duplication | High |
| **eksctl** | EKS cluster bootstrap (faster than Terraform for initial setup) | High |
| **Helm** | K8s application packaging and deployment | Must-have |
| **Helmfile** | Declarative multi-chart Helm deployments | Medium |
| **Kustomize** | Environment-specific K8s config overlays | Medium |

### 2. Container & Image Management

| Tool | Purpose | Priority |
|---|---|---|
| **Docker** + BuildKit | Container builds with layer caching | Must-have |
| **AWS ECR** | Container registry | Must-have |
| **Kaniko** | In-cluster Docker builds (no Docker daemon) | Medium |
| **Dive** | Analyse Docker image layer sizes | High (debugging) |
| **Trivy** | Container vulnerability scanning | High |
| **Cosign** | Container image signing (supply chain security) | Medium |

### 3. LLM & ML Model Serving

This is the biggest cost lever for this project:

| Tool | Purpose | Why for this project |
|---|---|---|
| **vLLM** | High-throughput LLM inference server | PagedAttention: 2-4x throughput vs raw HF. Continuous batching eliminates idle GPU time. OpenAI-compatible API — drop-in replacement for the OpenAI client in LLM inference service. |
| **NVIDIA Triton** | Multi-framework inference (PyTorch, TensorRT, ONNX) | For LayoutLMv2, DonutDet, embedding models — ensemble pipelines, dynamic batching |
| **Text Generation Inference (TGI)** | HuggingFace's LLM server | Alternative to vLLM; native HF model support |
| **BentoML** | ML model packaging + serving | Wrap reranker + embedding models as services |
| **Ray Serve** | Distributed model serving + request routing | Multi-model pipeline serving with resource sharing |
| **TorchServe** | PyTorch model serving | For DonutDet (detectron2-based model) |

**For this project specifically — vLLM is the single highest-impact change:**

```
Current: Raw HuggingFace pipeline
  → 1 request processed at a time
  → GPU 20-40% utilised between requests
  → KV cache not shared between requests
  → 35GB model loads on each pod restart

With vLLM:
  → Continuous batching: multiple requests processed simultaneously  
  → PagedAttention: KV cache managed like OS virtual memory
  → GPU 70-90% utilised
  → OpenAI-compatible API: zero code change in inference service
  → 2-4x throughput on same hardware = 50-75% cost reduction
```

### 4. GPU Optimization Stack

| Tool | Purpose | When to use |
|---|---|---|
| **bitsandbytes** | Runtime 4/8-bit quantization | Already in use — keep for local models |
| **AWQ (AutoAWQ)** | Offline 4-bit quantization, better quality than bitsandbytes | Pre-quantize Llama 3.1 70B → smaller model, faster load |
| **GPTQ** | Post-training quantization with calibration dataset | When AWQ not available for a model |
| **Flash Attention 2** | Memory-efficient attention (50% VRAM reduction in attention layers) | Add to all transformer inference — free performance |
| **TensorRT-LLM** | NVIDIA's optimised LLM inference engine | Maximum performance on NVIDIA GPUs — compile model to TensorRT |
| **NVIDIA MPS** | True GPU process sharing with memory isolation | Production-grade sharing for small models |
| **NVIDIA time-slicing** | Virtual GPU partitioning | Dev/test environments, simpler setup |
| **NVIDIA MIG** | Hardware-level GPU partitioning (A100/H100 only) | If using p4d.24xlarge — slice A100 into 7 MIG instances |

### 5. Experiment Tracking & Model Registry

| Tool | Purpose | Priority |
|---|---|---|
| **MLflow** | Experiment tracking, metric logging, model registry, artifact store | Must-have — free, self-hosted, integrates with HuggingFace |
| **DVC (Data Version Control)** | Git-like versioning for datasets and models stored in S3 | Must-have — critical for reproducibility |
| **Weights & Biases** | Richer experiment UI, hyperparameter sweeps, model comparison | High (paid but worth it for fine-tuning work) |
| **Hugging Face Hub** | Model versioning and sharing for internal fine-tuned models | Medium — use private HF Hub or S3 + MLflow |
| **LakeFS** | Git for data lakes — S3-compatible, branch/merge data | Medium — if data volumes are large |

### 6. Pipeline Orchestration

| Tool | Purpose | Priority |
|---|---|---|
| **Apache Airflow** | Schedule and orchestrate ingestion jobs, batch inference pipelines | High — already have cron jobs, Airflow replaces them |
| **Prefect** | Python-native orchestration, easier than Airflow | Alternative to Airflow |
| **Kubeflow Pipelines** | K8s-native ML pipeline DAGs | High — pipeline steps map 1:1 to existing microservices |
| **Argo Workflows** | K8s-native DAG runner (simpler than Kubeflow) | Medium |
| **Step Functions** | AWS-native workflow for SQS-triggered pipelines | Medium — already using SQS, Step Functions adds visibility |

### 7. Monitoring & Observability

| Tool | Purpose | Priority |
|---|---|---|
| **Prometheus** | Metrics collection | Must-have |
| **Grafana** | Dashboards (GPU util, inference latency, queue depth, cost) | Must-have |
| **NVIDIA DCGM Exporter** | GPU metrics → Prometheus | Must-have for GPU nodes |
| **Loki** | Log aggregation (replaces CloudWatch for app logs) | High |
| **Fluent Bit** | Log shipping from pods → Loki/CloudWatch | High |
| **Jaeger / Tempo** | Distributed tracing across microservices | Medium |
| **OpenTelemetry** | Vendor-neutral instrumentation SDK | Medium |
| **kube-state-metrics** | K8s object state metrics | Must-have |
| **node-exporter** | Node-level CPU/memory/disk metrics | Must-have |
| **Kubecost** | Per-namespace/pod cost attribution in Kubernetes | High — directly addresses client cost problem |
| **OpenCost** | Open-source Kubecost alternative | Alternative |

**Key Grafana dashboards to build for this project:**
- GPU utilisation per pod and per node group
- vLLM throughput (tokens/sec, batch size, queue wait time)
- SQS queue depth vs pod count (KEDA scaling proof)
- Cost per document processed (Kubecost + Prometheus)
- Embedding batch efficiency (chunks/sec vs GPU util)
- Model inference latency p50/p95/p99

### 8. GitOps & CI/CD

| Tool | Purpose | Priority |
|---|---|---|
| **ArgoCD** | GitOps — K8s state driven from Git, auto-sync | Must-have |
| **GitHub Actions** | CI pipelines — build, test, push image | Must-have |
| **Argo Rollouts** | Canary/blue-green deployments for model updates | High |
| **Skaffold** | Local dev K8s workflow (build → deploy → watch) | High |
| **Kyverno** | Policy as code — enforce resource limits, image scanning | Medium |
| **Trivy Operator** | Continuous vulnerability scanning of running images | Medium |

### 9. Data & Feature Management

| Tool | Purpose | Priority |
|---|---|---|
| **DVC** | Data version control with S3 backend | Must-have |
| **Delta Lake / Apache Iceberg** | ACID transactions on S3 data lake | Medium |
| **Great Expectations** | Data quality validation in pipeline | High |
| **Evidently AI** | ML model monitoring — data drift, embedding drift detection | High — critical for RAG quality |
| **LangSmith** | LLM application observability (traces, eval, feedback) | High — built for LangChain which is already in use |
| **Ragas** | RAG pipeline evaluation framework | High — evaluate retrieval quality, answer faithfulness |

### 10. LLM-Specific Operations (LLMOps)

| Tool | Purpose | Priority |
|---|---|---|
| **LangSmith** | Trace every LLM call, input/output logging, eval | High |
| **Ragas** | RAG evaluation: context recall, answer faithfulness, relevancy | High |
| **PromptFlow (Azure)** | Prompt versioning and testing | Medium |
| **Outlines** | Already in use — constrained JSON generation | Keep |
| **LiteLLM** | Universal LLM proxy — single API for OpenAI/Bedrock/Gemini/SLIP | High — replaces 5 separate client implementations |
| **Helicone** | LLM observability — cost tracking, cache, rate limiting | Medium |
| **Langfuse** | Open-source LLM observability (self-hosted alternative to LangSmith) | Medium |

**LiteLLM is particularly valuable here** — the LLM inference service has 5+ separate client implementations (OpenAI, Bedrock, Gemini, HorizonHub, SLIP). LiteLLM provides a single unified interface:

```python
# Replace this (5 different client classes):
if provider == "openai": client = OpenAIClient()
elif provider == "bedrock": client = BedrockClient()
elif provider == "gemini": client = GeminiClient()
...

# With this (one client, any provider):
from litellm import completion
response = completion(model="bedrock/meta.llama3-1-70b-instruct-v1:0", messages=[...])
response = completion(model="gpt-4o", messages=[...])
response = completion(model="gemini/gemini-2.0-flash", messages=[...])
```

---

## Infrastructure Provisioning Order

**This is the exact order to provision — each step enables the next.**

### Stage 1: Networking Foundation
```
1. VPC (3 AZ, public + private subnets)
2. NAT Gateways (private subnet internet access)
3. VPC Endpoints (S3, SQS, ECR, Bedrock — avoid NAT costs)
4. Security Groups (EKS, RDS, OpenSearch, bastion)
5. Route53 private hosted zone
```

### Stage 2: Data & Storage Layer
```
6.  S3 buckets (documents, models, configs, outputs, artifacts)
    → Lifecycle policies (IA after 30 days, Glacier after 90)
    → Versioning on model buckets
    → Bucket notifications → SQS (document upload triggers)
7.  EFS file system (model cache — ReadWriteMany)
    → Mount targets in all AZs
    → Access points per service
8.  RDS PostgreSQL (Multi-AZ, encrypted)
    → Parameter groups (pgvector if needed)
    → Automated snapshots
9.  OpenSearch domain (3 master, 3 data nodes)
    → Fine-grained access control
    → UltraWarm for older indices
10. Snowflake connection (existing — just IAM + PrivateLink)
```

### Stage 3: EKS Cluster
```
11. EKS cluster (v1.30+, private API endpoint)
    → aws-auth ConfigMap for team IAM roles
12. Node groups:
    a. System nodes (m5.large ×2 — CoreDNS, kube-proxy)
    b. CPU general (m5.2xlarge, spot, min=2 max=30)
    c. GPU small (g4dn.xlarge, min=0 max=10 via Karpenter)
    d. GPU large/LLM (g5.12xlarge, min=0 max=5 via Karpenter)
13. EKS add-ons:
    → VPC CNI (latest)
    → CoreDNS
    → kube-proxy
    → EBS CSI driver
    → EFS CSI driver
```

### Stage 4: Cluster Foundation Services
```
14. NVIDIA Device Plugin DaemonSet
    → Time-slicing ConfigMap for g4dn nodes
15. Karpenter
    → NodePool for GPU small (g4dn.xlarge/2xlarge)
    → NodePool for GPU large (g5.12xlarge) 
    → NodePool for CPU spot
    → Disruption budget policies
16. KEDA
    → SQS TriggerAuthentication (IRSA)
17. AWS Load Balancer Controller
18. External DNS
19. Cert-Manager (TLS certificates)
20. External Secrets Operator
    → ClusterSecretStore → AWS Secrets Manager
```

### Stage 5: Observability Stack
```
21. Prometheus + Grafana (kube-prometheus-stack Helm chart)
    → Persistent storage (EBS gp3)
    → AlertManager → PagerDuty/Slack
22. NVIDIA DCGM Exporter DaemonSet (GPU nodes only)
23. Loki + Fluent Bit
24. Kubecost
    → Integration with AWS Cost Explorer
25. Jaeger (tracing — optional initially)
```

### Stage 6: GitOps Layer
```
26. ArgoCD
    → Sync from Git repo (infra/k8s/ directory)
    → App of Apps pattern
    → RBAC per team
27. Argo Rollouts (canary for model deployments)
28. GitHub Actions runners (or self-hosted for private ECR)
```

### Stage 7: ML Platform
```
29. MLflow (self-hosted on EKS)
    → S3 artifact store
    → RDS metadata backend
    → Model registry
30. vLLM deployment (replaces raw HF inference)
    → OpenAI-compatible endpoint
    → PagedAttention config per model
31. NVIDIA Triton (embedding + reranker + classification models)
    → Model repository on EFS
    → Dynamic batching config per model
32. LangSmith / Langfuse (LLM observability)
33. Ragas evaluation pipeline
34. DVC (data versioning, S3 remote)
35. Airflow or Kubeflow Pipelines (replaces cron jobs)
```

### Stage 8: Application Deployment (in pipeline order)
```
36. Flask API (ALB + Ingress)
37. Preprocessing service (CPU, Spot)
38. Text Generation / Textract (CPU)
39. Linearization (CPU, Spot)
40. Prompt Generation (CPU, Spot)
41. Page Classification (GPU small, KEDA)
42. BBox Generation (GPU small, KEDA)
43. Chunking (GPU small, KEDA)
44. Context Retrieval (CPU, KEDA)
45. Context Reranking (GPU small, KEDA)
46. LLM Inference (GPU large, KEDA, vLLM)
47. QA System (CPU, HPA)
48. Text-to-SQL (CPU, KEDA)
49. Evaluation (CPU, scheduled)
```

---

## The Optimal EKS Architecture for This Project

```
                          ┌─────────────────────────────────────┐
                          │         AWS EKS Cluster             │
                          │                                     │
   Users ──→ ALB ──→ Flask API pod (CPU Spot)                  │
                    │                                           │
                    ↓ SQS                                       │
          ┌─────────────────────────────┐                       │
          │    CPU Node Pool (Spot)     │                       │
          │  Preprocessing  │  Linearize│                       │
          │  Text-Textract  │  Prompt   │                       │
          │  Ingestion Jobs │  Eval     │                       │
          └─────────────────────────────┘                       │
                    │ SQS                                        │
          ┌─────────────────────────────┐                       │
          │  GPU Small Pool (g4dn.xl)   │                       │
          │  [NVIDIA time-slicing ×4]   │                       │
          │  Chunking  │  Reranking     │                       │
          │  Page Class│  BBox Gen      │                       │
          │  (KEDA: scale 0→N on SQS)  │                       │
          └─────────────────────────────┘                       │
                    │ OpenSearch                                 │
          ┌─────────────────────────────┐                       │
          │  GPU Large Pool (g5.12xl)   │                       │
          │  vLLM server (Llama 3.1 70B)│                       │
          │  • PagedAttention           │                       │
          │  • Continuous batching      │                       │
          │  • AWQ 4-bit quantization   │                       │
          │  (KEDA: scale 0→8 on SQS)  │                       │
          └─────────────────────────────┘                       │
                    │                                            │
          ┌─────────────────────────────┐                       │
          │  Triton Inference Server    │                       │
          │  (GPU small pool)           │                       │
          │  • LayoutLMv2              │                       │
          │  • Embedding model          │                       │
          │  • Cross-encoder reranker   │                       │
          │  Dynamic batching per model │                       │
          └─────────────────────────────┘                       │
                                                                │
          ┌─────────────────────────────┐                       │
          │   Observability Namespace   │                       │
          │  Prometheus │ Grafana       │                       │
          │  DCGM Exporter │ Kubecost   │                       │
          │  Loki │ Fluent Bit          │                       │
          └─────────────────────────────┘                       │
                                                                │
          ┌─────────────────────────────┐                       │
          │   MLOps Namespace           │                       │
          │  MLflow │ ArgoCD            │                       │
          │  Airflow │ LangSmith        │                       │
          └─────────────────────────────┘                       │
                                                                │
          ┌─────────────────────────────────────────┐          │
          │           EFS (Model Cache)             │          │
          │  /models/llama-3.1-70b-awq/             │          │
          │  /models/layoutlmv2-client-a/           │          │
          │  /models/embedding-model/               │          │
          │  /models/reranker-mxbai/                │          │
          └─────────────────────────────────────────┘          │
                                                                │
          AWS: S3 │ SQS │ RDS │ OpenSearch │ Bedrock │ Textract│
                                                                │
          └─────────────────────────────────────────────────────┘
```

---

## Cost Impact: Before vs After

| Component | Current (estimated) | After optimization | Saving |
|---|---|---|---|
| LLM inference nodes | g5.12xl running 24/7 (~$16/hr) | KEDA scale-to-zero + vLLM batching | **~75% reduction** |
| Embedding/reranker | 4× g4dn.xl (one per model) | 1× g4dn.xl time-sliced ×4 | **~75% reduction** |
| CPU workloads | On-demand m5 | Spot instances | **~65% reduction** |
| Model cold starts | S3 download (5-10min × N pods) | EFS cache (30 sec) | **Eliminates waste** |
| GPU idle time | 60-80% idle (raw HF) | 20-30% idle (vLLM continuous batching) | **~60% GPU efficiency gain** |
| S3/ECR data transfer | Through NAT gateway ($0.045/GB) | VPC Endpoints (free) | **Eliminates transfer cost** |

Realistic total cost reduction: **60–80% lower monthly bill** with same or better throughput.

---

## Learning Priority Order (Summary)

```
Month 1:  Docker → Kubernetes → AWS core → EKS basics → Helm
Month 2:  Terraform → Karpenter → KEDA → NVIDIA device plugin → GPU time-slicing
Month 3:  vLLM → Triton → Flash Attention → AWQ quantization → EFS model cache
Month 4:  Prometheus/Grafana → DCGM → Kubecost → ArgoCD → GitHub Actions
Month 5:  MLflow → DVC → LangSmith → Ragas → Evidently AI
Month 6:  Kubeflow Pipelines → Argo Rollouts → OPA/Kyverno → LiteLLM → OpenTelemetry
```

**The single highest-ROI thing to do first:** Deploy **vLLM** instead of raw HuggingFace inference + **KEDA** for scale-to-zero. These two changes alone will cut GPU costs by 60-70% within days, before touching anything else.



## What is vLLM and Why This Project Desperately Needs It

### The Current Problem in This Project

Right now, `iqt_main_inference.py` loads a 70B parameter Llama model using raw HuggingFace `transformers` and processes messages one at a time from an SQS queue. Here is exactly what happens on the GPU every second:

```
SQS message arrives → model wakes up → GPU generates tokens → response done → GPU SITS IDLE → next message arrives → repeat
```

Between each SQS message, the GPU does absolutely nothing — but the EC2 instance (g5.12xlarge at ~$16/hour) keeps billing. GPU utilisation in this pattern is typically **15–25%**. You pay for 100% of the GPU but get productive work from only 15–25% of it. The rest is idle time — pure wasted money.

There is a second problem. HuggingFace's raw inference pipeline has no memory management for the **KV cache** (Key-Value cache). Every transformer layer during generation stores intermediate attention states in GPU memory. With raw HuggingFace, each request gets a fixed pre-allocated block of VRAM regardless of whether it uses all of it. When two requests try to run simultaneously, they fight over VRAM and one gets killed — or the system serialises them anyway. This is why the current code processes one request at a time. It is the only safe way with raw HuggingFace.

### What vLLM Is

vLLM is a purpose-built LLM inference server from UC Berkeley. It solves both problems above with two core innovations:

**PagedAttention** — vLLM manages KV cache memory exactly like an operating system manages RAM with virtual memory paging. Instead of pre-allocating a fixed block per request, it allocates KV cache in small pages and hands them out dynamically as tokens are generated. This means 10, 20, or 50 requests can share the same GPU VRAM simultaneously without any one request blocking another. The GPU is always doing work.

**Continuous Batching** — In raw HuggingFace, you wait for one request to completely finish before starting another. vLLM runs a server that accepts incoming requests continuously and inserts new requests mid-generation into the batch. As soon as one sequence finishes, a new one takes its slot immediately. The GPU never goes idle between requests.

The result: the same g5.12xlarge that currently handles 1 request at a time handles 10–50 simultaneous requests with vLLM. GPU utilisation goes from ~20% to ~75–85%. You do not need to change the EC2 instance — you get 10–50x more throughput from hardware you are already paying for.

vLLM exposes an OpenAI-compatible REST API. The existing inference code needs zero changes to the request/response format — you just point it at `http://iqt-vllm:8000/v1` instead of calling HuggingFace locally.

### The Cost Impact in This Specific Project

The contracts-ai-iqt pipeline is batch/async — documents come in via SQS, get processed, results go back to S3/RDS. This means:

- **During business hours**: bursts of many documents queued up simultaneously — vLLM batches all of them together, GPU runs at 80%+
- **At night/weekends**: zero documents in queue — with KEDA, the vLLM pod scales to zero and the g5.12xlarge node terminates (Karpenter removes it). Zero billing.

Without vLLM, even if you add KEDA scale-to-zero, each document still takes the same wall-clock time because requests are serialised. With vLLM, 20 documents process in nearly the same time as 1 document (they run in parallel in the batch). This means the GPU node is needed for a much shorter total time per day, amplifying the KEDA savings further.

---

## What is NVIDIA Triton and Why This Project Needs It

### The Current Problem for Non-LLM Models

This project has four services that run smaller GPU models:

- **Chunking service**: embedding model (BGE/sentence-transformers, ~110–560M params)
- **Page classification**: LayoutLMv2 (~200M params)
- **BBox generation**: DonutDet/DETR (~200M params)
- **Context reranking**: mxbai-rerank-large-v1 (~350M), bge-reranker-v2-m3 (~568M)

Each service currently runs as a separate ECS task with its own dedicated GPU. A T4 GPU has 16GB of VRAM. The embedding model uses ~2GB. The reranker uses ~3GB. LayoutLMv2 uses ~2GB. DonutDet uses ~4GB. Total GPU memory actually needed across all four: **~11GB**.

Currently they occupy **four separate T4 GPUs = 64GB of VRAM to hold 11GB of models**. The other 53GB of VRAM sits completely empty. Four g4dn.xlarge instances run 24/7. Each costs ~$0.526/hour, so four of them = ~$2.10/hour, ~$50/day, ~$1,500/month — just for models that collectively fit on a single GPU.

There is a second problem: no dynamic batching. When 5 documents need embedding at the same time, the chunking service's raw HuggingFace code processes them one by one through the model. The GPU is batch-capable but the code does not exploit it.

### What NVIDIA Triton Is

Triton is a production inference server from NVIDIA that solves both problems:

**Multi-framework, multi-model serving on a single GPU** — Triton can load LayoutLMv2 (PyTorch), DonutDet (PyTorch), the embedding model (PyTorch), and both rerankers simultaneously on one GPU. It manages VRAM allocation between all models. One g4dn.xlarge running Triton replaces four g4dn.xlarge instances running separate services.

**Dynamic batching per model** — Triton has a built-in dynamic batcher for each model. When embedding requests arrive, Triton accumulates them for a configurable microsecond window (e.g., 5ms) and processes the entire batch in one forward pass. A batch of 16 embedding requests takes almost the same GPU time as a batch of 1 because transformer models are highly parallelisable. This turns single-request sequential processing into high-throughput batch processing automatically, with no code changes in your services.

**Model ensemble pipelines** — Triton can chain models. For this project: input text → embedding model → reranker → return score. This entire pipeline runs inside Triton with GPU tensors transferred in-memory between models, never touching the CPU or network between steps.

### The Combined Cost Impact

With Triton:
- 4 separate g4dn.xlarge instances (4 GPUs, ~$1,500/month) → 1 g4dn.xlarge instance (1 GPU, ~$378/month)
- Processing speed increases 5–15x due to dynamic batching
- Because processing is faster, KEDA scales the node to zero sooner each day, saving further

Estimated saving from Triton alone: ~$1,100/month on GPU instances, not counting the throughput multiplier effects.

---

## Why Both Are the Highest-Priority Changes

The root cause of the GPU waste in this project is that it was built the way every ML project starts — raw HuggingFace inference, one model per machine, one request at a time. This is fine for development. In production at scale it is dramatically inefficient.

**vLLM fixes the LLM (Llama 3.1 70B)** — turns a 20% utilised g5.12xlarge into an 80% utilised one handling 10–50x more concurrent requests.

**Triton fixes all the smaller models** — consolidates 4 GPU instances into 1 and adds automatic dynamic batching.

Together, these two changes address the majority of the GPU cost problem **without changing a single line of application business logic**. The existing `iqt_main_inference.py` stays exactly as-is — it just points its HTTP calls to vLLM instead of calling HuggingFace locally. The chunking/reranking/classification services similarly just call Triton's HTTP endpoint instead of running models in-process.