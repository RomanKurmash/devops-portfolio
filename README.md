🚀 DevOps Portfolio: Production-Ready Infrastructure Automation

This repository hosts the source code and configuration for my personal DevOps infrastructure. It demonstrates a complete lifecycle of a containerized application—from automated deployment with Jenkins to advanced observability with Prometheus, Grafana, and Loki.

Live Demo: devops-portfolio.pp.ua
🏗️ System Architecture

The project implements a microservices architecture focused on security (Zero Trust) and full system transparency (Observability).
Key Components:

    Web Stack: WordPress + MySQL with persistent data volumes.

    Reverse Proxy: Nginx with automated container discovery and SSL termination.

    Connectivity: Cloudflare Tunnels (Zero Trust) to securely expose local services to the internet without opening any inbound ports on the host router.

    CI/CD: Jenkins (Pipeline-as-Code) utilizing Docker-outside-Docker (DooD) for infrastructure management.

    Observability: Integrated Prometheus (metrics) and Grafana (dashboards) with Loki & Promtail for centralized logging.

## 🛠️ Technology Stack

| Category | Tools & Technologies | Focus Area |
| :--- | :--- | :--- |
| **Infrastructure** | 🐳 Docker, Docker Compose, Ubuntu 24.04 | Containerization & OS |
| **Networking** | 🌐 Nginx, Cloudflare Tunnels, SSL/TLS | Zero Trust & Secure Access |
| **CI/CD** | 🏗️ Jenkins, Groovy Pipelines, Git/GitHub | Automation & Pipelines |
| **Observability** | 📊 Prometheus, Grafana, Loki, Promtail | Metrics & Centralized Logging |
| **Security** | 🛡️ Linux Hardening, Firewall (UFW) | System Protection |

⚡ CI/CD Pipeline Logic

The entire deployment is automated via a Jenkinsfile, ensuring a "Single Source of Truth" approach.

    Setup & Secrets: Workspace cleanup and secure injection of .env variables via Jenkins Credentials.

    Smart Cleanup: Removal of orphaned containers and unused Docker images to maintain host health.

    Deploy Infrastructure: Orchestrating multi-container stacks using Docker Compose.

    Health Checks: Automated validation of service availability (Nginx, WP, DB, Grafana, etc.) before marking the build as successful.

📊 Monitoring & Centralized Logging

I believe that "if it's not monitored, it's not in production."

    Metrics: Prometheus scrapes real-time data from the Docker host and containers.

    Logging: Grafana Loki and Promtail are used to aggregate logs. This eliminates the need to SSH into the server to debug—all logs are searchable within Grafana using LogQL.

    Troubleshooting: Successfully resolved complex Docker bind-mount issues related to path mismatches in DooD environments, ensuring config persistence across deployments.

👨‍💻 About the Author

I am a 4th-year Cybersecurity student with a deep passion for Infrastructure as Code (IaC) and automation.

    🦾 Discipline: I balance my academic studies with physically demanding work in construction. This has forged a high level of endurance and a 24/7 "get it done" mindset.

    🎯 Objective: Transitioning into a Junior DevOps Engineer role where I can apply my troubleshooting skills and build resilient systems.

    📫 Connect with me: LinkedIn | Djinni

🔧 Local Development

    Clone the repository:
    Bash

git clone https://github.com/RomanKurmash/devops-portfolio.git

Configure your .env file based on the provided template.

Launch the stack:
Bash

docker compose up -d
