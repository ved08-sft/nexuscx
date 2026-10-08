# ERUDITE 2026 - Internship Presentation Outline
## NexusCX Project

## Slide 1: Title Slide
- **Name:** [Your Name]
- **Course and College/University:** [Your Course and Institution]
- **Company/Organization Name:** MAS Callnet India Pvt. Ltd.
- **Internship Role:** [e.g., AI/ML Engineering Intern, Software Engineering Intern]
- **Internship Duration:** [Start Date] to [End Date]
- **Internship Completion Certificate:** [Available/Not Available]

## Slide 2: About the Organization
- **Brief profile:** MAS Callnet India Pvt. Ltd. is a hybrid BPO/KPO/CX enterprise
- **Industry/Sector:** Business Process Outsourcing/Knowledge Process Outsourcing/Customer Experience (BPO/KPO/CX)
- **Nature of business:** 
  - Inbound/outbound contact centers
  - eKYC validation
  - BFSI document processing
  - Back-office verticals: Shipment tracking, flight disruption & refunds, HR outsourcing
- **Key products/services:**
  - CallMaster™ (voice bots, prompt coaching, audio transcripts)
  - NexusCX: Next-Gen Autonomous Back-Office & Quality Intelligence Engine (developed during internship)

## Slide 3: Internship Objectives
- **Purpose of the internship:** To contribute to the development of NexusCX, a Next-Gen Autonomous Back-Office & Quality Intelligence Engine that extends CallMaster™ capabilities
- **Key objectives and expectations:**
  - Learn and apply AI/ML engineering practices in a real-world enterprise setting
  - Contribute to the LangGraph-based agentic orchestration system
  - Work on WEKA ML pipeline for risk prediction
  - Develop/polish Next.js frontend components for agent and supervisor interfaces
  - Understand and implement human-in-the-loop (HITL) principles
- **Areas of learning and exposure:**
  - Microservices architecture with Docker and FastAPI
  - Real-time communication via WebSockets
  - Retrieval-Augmented Generation (RAG) with ChromaDB
  - ML model integration and inference (WEKA J48/Random Forest)
  - Agent-based AI systems (LangGraph)
  - Frontend development with Next.js, TypeScript, and Tailwind CSS

## Slide 4: Roles and Responsibilities
- **Major tasks handled:**
  - Setting up local development infrastructure with Docker containers
  - Implementing the Local RAG Pipeline (ChromaDB + FastEmbed)
  - Developing WEKA Model Integration for risk prediction
  - Creating synthetic data generation scripts
  - Implementing JVM-based WEKA runner with Python fallback
  - Building risk calculation engine
  - Writing and verifying contract unit tests
- **Projects/assignments undertaken:**
  - NexusCX Project - Next-Gen Autonomous Back-Office & Quality Intelligence Engine
    - Phase 1: Local Infrastructure, Containers & Core Setup (Completed)
    - Phase 2: Local RAG Pipeline & WEKA Model Integration (Significant Progress)
    - Phase 3: LangGraph Agentic Engine & Fail-Safe Routing (In Progress)
- **Tools, software, techniques, or methodologies used:**
  - Backend: Python 3.11+, FastAPI, Docker, LangGraph, WEKA, ChromaDB, Redis, SQLite
  - Frontend: Next.js 14, TypeScript, Tailwind CSS, WebSockets
  - ML: WEKA (J48, Random Forest), FastEmbed (all-MiniLM-L6-v2)
  - Testing: Pytest, Playwright
  - DevOps: Docker Compose, Git, GitHub
  - Architecture: Microservices, Event-driven design, Human-in-the-Loop (HITL)
- **Your individual contribution:**
  - Completed Phase 1: Scaffolded backend structure, implemented Pydantic v2 schemas for all REST endpoints, wrote and verified 15 contract unit tests (100% passing), created Docker configuration, configured development tools (ESLint, Flake8, Mypy)
  - Made significant progress on Phase 2: 
    - Implemented RAG store with ChromaDB and FastEmbed for semantic search
    - Developed RAG ingest CLI for processing PDF/DOCX SOP files
    - Created synthetic data generation scripts for WEKA training
    - Implemented WEKA training script and model interface with JVM management
    - Built Python J48 inference fallback for when JVM is unavailable
    - Developed risk calculation engine for escalation prediction
    - Integrated all components with proper error handling and logging

## Slide 5: Industry Learning and Insights
- **Key industry-specific learnings:**
  - How AI/ML technologies are applied in BPO/KPO/CX to transform manual processes into intelligent automation
  - The importance of Human-in-the-Loop (HITL) systems in maintaining quality and compliance while leveraging AI
  - Real-time analytics and monitoring needs in customer service operations
  - Integration challenges between legacy systems (CallMaster™) and new AI extensions
- **Practical exposure gained:**
  - End-to-end development of an AI-powered enterprise system
  - Working with microservices architecture and inter-service communication
  - Implementing ML models in production environments with fallback mechanisms
  - Building real-time dashboards for agent and supervisor interfaces
  - Applying software engineering best practices in a professional setting
- **Application of academic concepts in the workplace:**
  - Applied machine learning concepts (feature engineering, model training/inference) to real business problems
  - Used software architecture patterns (microservices, event-driven) learned in academics
  - Applied database concepts (SQL vs NoSQL, caching strategies) in system design
  - Utilized software testing methodologies (TDD, contract testing) to ensure quality
- **Difference between classroom learning and industry practices:**
  - Classroom: Focus on theoretical concepts and isolated exercises
  - Industry: Emphasis on practical implementation, scalability, reliability, and business value
  - Industry requires considering edge cases, error handling, and system robustness
  - Industry values deliverables that solve actual business problems with measurable impact

## Slide 6: Problem/Challenge Identified
- **Business/operational challenge observed:** 
  - After-call manual work in BPO/KPO operations leads to inefficiencies and errors
  - CallMaster™ system stops at conversation, leaving post-call work entirely to human agents
- **Background and significance of the problem:**
  - High Average Handling Time (AHT) due to tab-switching and SOP lookup (estimated 40% of handle time is non-conversational work)
  - Low Quality Assurance (QA) coverage ≈ 2-5% because QA is manual sampling; compliance breaches often go undetected
  - Reactive escalation: churn and escalation issues are discovered only after customers complain
  - Agents spend valuable time searching through 100+ page SOP PDFs mid-call, forgetting regulatory disclosures, and performing repetitive checks
- **Why the issue required attention:**
  - Direct impact on operational costs and efficiency
  - Compliance risks with potential regulatory penalties
  - Poor customer experience leading to churn and dissatisfaction
  - Limited ability to prove compliance to clients without systematic auditing
  - Need for proactive rather than reactive customer service management

## Slide 7: Analysis and Problem-Solving Approach
- **Approach adopted to understand the problem:**
  - Studied the existing CallMaster™ workflow and identified manual bottlenecks
  - Reviewed SOPs and compliance requirements specific to BFSI document processing
  - Analyzed pain points reported by agents, QA managers, and operations directors
  - Researched AI/ML solutions applicable to back-office automation
- **Data, research, or analytical methods used:**
  - Requirements gathering from stakeholders (agents, supervisors, directors)
  - Process analysis of current manual workflows
  - Technology evaluation for AI/ML stack (LLMs, vector databases, ML frameworks)
  - Architecture design sessions to define system components and interactions
- **Key findings:**
  - Post-call work can be significantly automated while keeping humans in the loop for final approval
  - Real-time risk scoring can enable proactive intervention before escalation occurs
  - Integrated SOP retrieval reduces agent search time and improves accuracy
  - Comprehensive compliance auditing (100% coverage) is achievable with automated checking
  - A unified system providing agents with AI suggestions and supervisors with live monitoring improves both efficiency and quality
- **Your contribution toward addressing the problem:**
  - Contributed to building the NexusCX system that directly addresses these challenges:
    - Automated intent classification and SOP retrieval reduces agent workload
    - Real-time compliance monitoring provides 100% QA coverage
    - WEKA-based risk prediction enables proactive escalation prevention
    - Human-in-the-Loop design ensures agents remain in control of AI suggestions
    - Live dashboards give supervisors visibility into ongoing sessions and risk levels

## Slide 8: Innovation and Recommendations
- **Ideas or improvements proposed:**
  - NexusCX implements a novel combination of technologies:
    - LangGraph-based multi-agent orchestration for complex workflow management
    - Hybrid RAG system (dense + BM25 with RRF) for accurate SOP retrieval
    - WEKA ML pipeline with JVM/Python fallback for reliable risk prediction in varying environments
    - Real-time WebSocket architecture for live agent/supervisor interfaces
    - Comprehensive compliance checking with deterministic and LLM-based rules
  - The system maintains human agency while leveraging AI for augmentation
- **Practical recommendations:**
  - Continue development and testing of Phase 3 (LangGraph Agentic Engine) and Phase 4 (WebSockets & Next.js Dashboard)
  - Conduct user acceptance testing with actual agents and supervisors to refine the UI/UX
  - Plan for gradual rollout starting with pilot groups before enterprise-wide deployment
  - Establish feedback loops for continuous improvement based on real-world usage
  - Consider extending the system to other verticals beyond flight disruption and eKYC
- **Feasibility of the proposed solution:**
  - Demonstrated through working prototypes in Phases 1 and 2
  - Uses open-source and free-tier technologies to minimize licensing costs
  - Modular architecture allows for incremental development and testing
  - Successfully integrated with mock back-office APIs simulating real systems
  - Validated through contract unit tests (15/15 passing in Phase 1)
- **Expected impact on the organization:**
  - **Reduce AHT by 25%** through pre-drafted responses and automated tool calls
  - **Achieve 100% QA coverage** via Compliance Guardrail Agent
  - **Prevent escalations** with alerts ≥90 seconds before escalation point
  - **Maintain zero licensing cost** using free-tier/open-source stack only
  - Improve agent efficiency and reduce cognitive load
  - Enhance compliance and provide auditable trails for client verification
  - Enable data-driven decision making through PowerBI analytics export

## Slide 9: Key Achievements and Learning
- **Major outcomes or achievements:**
  - Successfully completed Phase 1: Local Infrastructure, Containers & Core Setup
    - 15/15 contract unit tests passing
    - Fully functional Docker-based development environment
    - Complete REST API schema validation with Pydantic v2
  - Made significant progress on Phase 2: Local RAG Pipeline & WEKA Model Integration
    - Functional RAG store with ChromaDB and FastEmbed for semantic search
    - Working RAG ingest CLI for SOP document processing
    - Synthetic data generation pipeline for WEKA model training
    - WEKA model interface with JVM management and Python J48 fallback
    - Implemented risk calculation engine for escalation prediction
  - Established foundation for Phase 3 development (LangGraph Agentic Engine)
- **Skills developed:**
  - Technical: Python/FastAPI, Next.js/TypeScript, Docker, LangGraph, WEKA, ChromaDB, Redis, WebSockets
  - ML: Model training/inference, feature engineering, risk scoring
  - Architecture: Microservices design, event-driven systems, HITL patterns
  - Professional: Agile development practices, TDD, code reviews, documentation
  - Problem-solving: Debugging complex systems, performance optimization, integration testing
- **Professional and personal learning:**
  - Gained experience in building production-grade AI systems for enterprise use
  - Learned to balance innovation with reliability and maintainability
  - Developed communication skills for technical collaboration in remote settings
  - Strengthened ability to learn and apply new technologies quickly
  - Appreciation for the importance of user-centered design in AI systems
- **Measurable results, wherever applicable:**
  - Phase 1: 15/15 contract unit tests passing (100% success rate)
  - Docker containers successfully built and orchestrated via docker-compose
  - REST API endpoints properly validated with Pydantic schemas
  - ChromaDB integration verified with sample SOP documents
  - WEKA model training pipeline established with synthetic data
  - Risk calculation engine producing scores in [0,1] range

## Slide 10: Conclusion
- **Key takeaway from the internship:** 
  - Experience in designing and building AI-powered enterprise systems that augment human capabilities rather than replace them
  - Understanding of how to implement sophisticated AI systems with proper governance, transparency, and human control
- **Overall learning experience:**
  - Highly valuable and challenging opportunity to work on cutting-edge AI technology
  - Exposure to full lifecycle development from requirements to implementation
  - Appreciation for the complexities of deploying AI in real-world business environments
  - Reinforced passion for AI/ML engineering and software architecture
- **How the internship contributed to your future career goals:**
  - Provided concrete experience in enterprise AI system development
  - Built technical skills directly applicable to AI/ML engineering roles
  - Enhanced understanding of production system design and deployment
  - Strengthened problem-solving abilities in complex technical environments
  - Clarified career interest in AI systems that combine technical excellence with business impact
  - Prepared for roles in AI engineering, ML engineering, or software architecture focused on intelligent systems

---

## Presentation Notes:
- **Duration:** 7-8 minutes (approximately 40-50 seconds per slide)
- **Visuals:** Use charts, graphs, diagrams, and screenshots where appropriate
- **Focus:** Emphasize individual contribution and learning
- **Style:** Professional, structured, and visually clean
- **Confidentiality:** Do not disclose company-sensitive or proprietary information
- **Accuracy:** Ensure all data, figures, and information presented are accurate and relevant