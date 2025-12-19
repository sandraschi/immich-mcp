# Unified Monitoring Stack for All MCP Repositories

**Date:** October 23, 2025  
**Purpose:** Single monitoring stack serving all MCP repositories and applications

---

## 🎯 **Vision: One Stack to Rule Them All**

Create a **single, centralized monitoring stack** that serves:
- **All MCP Servers** (tailscale-mcp, virtualization-mcp, database-operations-mcp, etc.)
- **MyAI Platform** (dashboard, calibre-plus, document-viewer, etc.)
- **VeoGen Platform** (video generation, music generation, etc.)
- **Home Infrastructure** (tapo-cameras, nest-protect, ring devices, etc.)
- **Future Projects** (any new MCP servers or applications)

---

## 🏗️ **Unified Architecture**

### **Core Components**
```
┌─────────────────────────────────────────────────────────────┐
│                    UNIFIED MONITORING STACK                │
├─────────────────────────────────────────────────────────────┤
│  Grafana (Port 3000) - Single Dashboard for Everything     │
│  ├── MCP Servers Dashboard                                 │
│  ├── MyAI Platform Dashboard                               │
│  ├── VeoGen Platform Dashboard                             │
│  ├── Home Infrastructure Dashboard                         │
│  └── System Overview Dashboard                             │
├─────────────────────────────────────────────────────────────┤
│  Prometheus (Port 9090) - Central Metrics Collection       │
│  ├── MCP Server Metrics                                    │
│  ├── Application Metrics                                   │
│  ├── System Metrics                                        │
│  └── Custom Business Metrics                               │
├─────────────────────────────────────────────────────────────┤
│  Loki (Port 3100) - Central Log Aggregation                │
│  ├── Structured Logs from All Applications                 │
│  ├── MCP Server Logs                                       │
│  ├── Application Logs                                      │
│  └── System Logs                                           │
├─────────────────────────────────────────────────────────────┤
│  Promtail (Port 9080) - Log Collection Agent               │
│  ├── File-based Log Collection                             │
│  ├── Docker Log Collection                                 │
│  ├── System Log Collection                                 │
│  └── Application Log Collection                            │
├─────────────────────────────────────────────────────────────┤
│  RebootX On-Prem (Port 8080) - Mobile Monitoring          │
│  ├── Mobile Grafana Access                                 │
│  ├── Push Notifications                                    │
│  ├── Mobile Dashboards                                     │
│  └── Remote Monitoring                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 **Current State Analysis**

### **Existing Monitoring Infrastructure**

#### **MyAI Platform**
- ✅ **Grafana**: Port 3140
- ✅ **Loki**: Port 3100  
- ✅ **Promtail**: Running
- ✅ **Docker Network**: `mywienerlinien_loki-network`
- ✅ **Applications**: 5+ applications with logging integration

#### **VeoGen Platform**
- ✅ **Grafana**: Port 3000
- ✅ **Prometheus**: Port 9090
- ✅ **Loki**: Port 3100
- ✅ **Promtail**: Running
- ✅ **Applications**: Backend, Frontend, MCP servers

#### **Tailscale MCP**
- ✅ **Grafana**: Port 3000
- ✅ **Prometheus**: Port 9091
- ✅ **Loki**: Port 3100
- ✅ **Promtail**: Running
- ✅ **Applications**: MCP server with comprehensive metrics

### **Port Conflicts Identified**
- **Grafana**: MyAI (3140) vs VeoGen (3000) vs Tailscale (3000)
- **Prometheus**: VeoGen (9090) vs Tailscale (9091)
- **Loki**: All using 3100 ✅ (Good!)

---

## 🔧 **Unification Strategy**

### **Phase 1: Port Standardization**
```
Service          Current Ports           Unified Port
─────────────────────────────────────────────────────
Grafana         3140, 3000, 3000  →     3000
Prometheus      9090, 9091        →     9090
Loki           3100, 3100, 3100   →     3100 ✅
Promtail       9080, 9080, 9080   →     9080 ✅
RebootX On-Prem N/A               →     8080 (new)
```

### **Phase 2: Network Unification**
- **Single Docker Network**: `unified-monitoring-network`
- **Shared Volumes**: Centralized configuration and data storage
- **Service Discovery**: All services can communicate within the network

### **Phase 3: Configuration Consolidation**
- **Single Docker Compose**: `docker-compose.monitoring.yml`
- **Unified Prometheus Config**: All targets in one configuration
- **Unified Loki Config**: All log sources in one configuration
- **Unified Grafana**: All dashboards in one instance

---

## 📋 **Implementation Plan**

### **Step 1: Create Unified Docker Compose**
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    networks:
      - unified-monitoring

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - unified-monitoring

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki/loki.yml:/etc/loki/local-config.yaml
      - loki-data:/loki
    networks:
      - unified-monitoring

  promtail:
    image: grafana/promtail:latest
    ports:
      - "9080:9080"
    volumes:
      - ./promtail/promtail.yml:/etc/promtail/config.yml
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    networks:
      - unified-monitoring

  rebootx-on-prem:
    image: rebootx/on-prem:latest
    ports:
      - "8080:8080"
    environment:
      - GRAFANA_URL=http://grafana:3000
      - GRAFANA_USER=admin
      - GRAFANA_PASSWORD=admin
    networks:
      - unified-monitoring

volumes:
  grafana-data:
  prometheus-data:
  loki-data:

networks:
  unified-monitoring:
    driver: bridge
```

### **Step 2: Unified Prometheus Configuration**
```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # MCP Servers
  - job_name: 'tailscale-mcp'
    static_configs:
      - targets: ['tailscale-mcp:9091']
  
  - job_name: 'virtualization-mcp'
    static_configs:
      - targets: ['virtualization-mcp:9091']
  
  - job_name: 'database-operations-mcp'
    static_configs:
      - targets: ['database-operations-mcp:9091']

  # MyAI Platform
  - job_name: 'myai-dashboard'
    static_configs:
      - targets: ['myai-dashboard:8000']
  
  - job_name: 'myai-calibre-plus'
    static_configs:
      - targets: ['myai-calibre-plus:8000']

  # VeoGen Platform
  - job_name: 'veogen-backend'
    static_configs:
      - targets: ['veogen-backend:8000']
  
  - job_name: 'veogen-frontend'
    static_configs:
      - targets: ['veogen-frontend:3000']

  # System Metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
  
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
```

### **Step 3: Unified Loki Configuration**
```yaml
# loki/loki.yml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 5m
  chunk_retain_period: 30s
  max_transfer_retries: 0

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 168h

storage_config:
  boltdb:
    directory: /loki/index

  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  max_cache_freshness_per_query: 10m
  split_queries_by_interval: 15m
  max_query_parallelism: 32
  max_streams_per_user: 0
  max_global_streams_per_user: 0
  ingestion_rate_mb: 16
  ingestion_burst_size_mb: 32
  per_stream_rate_limit: 3MB
  per_stream_rate_limit_burst: 15MB
  max_line_size: 256000
  max_line_size_truncate: true
```

### **Step 4: Unified Promtail Configuration**
```yaml
# promtail/promtail.yml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # MCP Server Logs
  - job_name: mcp-servers
    static_configs:
      - targets:
          - localhost
        labels:
          job: mcp-servers
          __path__: /var/log/mcp/*.log

  # MyAI Application Logs
  - job_name: myai-apps
    static_configs:
      - targets:
          - localhost
        labels:
          job: myai-apps
          __path__: /var/log/myai/*.log

  # VeoGen Application Logs
  - job_name: veogen-apps
    static_configs:
      - targets:
          - localhost
        labels:
          job: veogen-apps
          __path__: /var/log/veogen/*.log

  # Docker Container Logs
  - job_name: docker-containers
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
        filters:
          - name: label
            values: ["logging=promtail"]
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/?(.*)'
        target_label: 'container_name'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'logstream'
      - source_labels: ['__meta_docker_container_label_logging_job_name']
        target_label: 'job'
```

---

## 🎨 **Unified Grafana Dashboards**

### **Dashboard Structure**
```
📊 Unified Monitoring Dashboard
├── 🏠 Home Infrastructure
│   ├── Tapo Cameras & Security
│   ├── Nest Protect & Ring Devices
│   ├── Energy Monitoring (Smart Plugs)
│   └── Environmental Sensors
├── 🤖 MCP Servers
│   ├── Tailscale Network Monitoring
│   ├── Virtualization Management
│   ├── Database Operations
│   └── System Administration
├── 🎬 VeoGen Platform
│   ├── Video Generation Pipeline
│   ├── Music Generation Pipeline
│   ├── User Activity & Usage
│   └── Resource Utilization
├── 🧠 MyAI Platform
│   ├── Dashboard Performance
│   ├── Calibre Plus Operations
│   ├── Document Viewer Activity
│   └── Gemini Tools Usage
└── 🖥️ System Overview
    ├── Infrastructure Health
    ├── Resource Usage
    ├── Network Performance
    └── Security Monitoring
```

---

## 📱 **Mobile Monitoring with RebootX**

### **RebootX On-Prem Integration**
- **Self-hosted RebootX**: Port 8080
- **Grafana Integration**: Direct connection to unified Grafana
- **Mobile Dashboards**: Optimized for iPad/iPhone viewing
- **Push Notifications**: Alerts for critical issues
- **Remote Access**: Monitor from anywhere

### **Mobile Dashboard Features**
- **Home Security**: Tapo cameras, alarms, sensors
- **Infrastructure**: Server health, network status
- **Applications**: MCP servers, VeoGen, MyAI
- **System**: CPU, memory, disk, network usage

---

## 🚀 **Migration Strategy**

### **Phase 1: Preparation (Week 1)**
1. **Backup Current Configurations**: Save all existing monitoring configs
2. **Create Unified Directory**: Set up centralized monitoring structure
3. **Test in Isolation**: Deploy unified stack in test environment

### **Phase 2: Gradual Migration (Week 2-3)**
1. **Start with New Projects**: Use unified stack for new MCP servers
2. **Migrate MyAI**: Move MyAI monitoring to unified stack
3. **Migrate VeoGen**: Move VeoGen monitoring to unified stack
4. **Migrate Tailscale**: Move Tailscale monitoring to unified stack

### **Phase 3: Full Integration (Week 4)**
1. **Deploy RebootX On-Prem**: Set up mobile monitoring
2. **Create Unified Dashboards**: Consolidate all dashboards
3. **Set up Alerts**: Configure comprehensive alerting
4. **Documentation**: Update all documentation

---

## 💰 **Cost Benefits**

### **Resource Optimization**
- **Single Grafana Instance**: Instead of 3+ separate instances
- **Single Prometheus Instance**: Instead of 2+ separate instances
- **Single Loki Instance**: Instead of 3+ separate instances
- **Shared Infrastructure**: Reduced resource consumption

### **Maintenance Benefits**
- **Single Configuration**: One place to manage all monitoring
- **Unified Updates**: Update once, benefit everywhere
- **Centralized Logging**: All logs in one place
- **Consistent Dashboards**: Standardized monitoring across all projects

---

## 🔒 **Security Considerations**

### **Access Control**
- **Grafana Authentication**: Single sign-on for all dashboards
- **Network Isolation**: Secure communication between services
- **API Keys**: Centralized management of monitoring credentials
- **Audit Logging**: Track all monitoring access and changes

### **Data Protection**
- **Log Retention**: Configurable retention policies
- **Data Encryption**: Encrypted communication between services
- **Backup Strategy**: Regular backups of monitoring data
- **Disaster Recovery**: Recovery procedures for monitoring stack

---

## 📈 **Success Metrics**

### **Technical Metrics**
- **Uptime**: 99.9% monitoring stack availability
- **Performance**: < 1s dashboard load times
- **Coverage**: 100% of applications monitored
- **Alert Response**: < 5 minutes for critical alerts

### **Operational Metrics**
- **Maintenance Time**: 50% reduction in monitoring maintenance
- **Setup Time**: 80% reduction in new project monitoring setup
- **Resource Usage**: 40% reduction in total monitoring resources
- **User Satisfaction**: Improved monitoring experience across all projects

---

## 🎯 **Next Steps**

### **Immediate Actions**
1. **Create Unified Directory**: Set up centralized monitoring structure
2. **Design Unified Docker Compose**: Create single monitoring stack
3. **Plan Migration Strategy**: Detailed migration plan for each repository
4. **Set up Test Environment**: Deploy unified stack for testing

### **Short-term Goals (1-2 weeks)**
1. **Deploy Unified Stack**: Production deployment of unified monitoring
2. **Migrate First Repository**: Start with one repository as proof of concept
3. **Create Unified Dashboards**: Develop comprehensive dashboards
4. **Set up RebootX On-Prem**: Deploy mobile monitoring solution

### **Long-term Goals (1-2 months)**
1. **Complete Migration**: All repositories using unified monitoring
2. **Advanced Features**: Implement advanced monitoring features
3. **Automation**: Automated monitoring setup for new projects
4. **Documentation**: Comprehensive documentation and training

---

**Status**: 📋 Planning Phase  
**Priority**: 🔥 High  
**Estimated Effort**: 2-3 weeks  
**Expected Benefits**: Significant cost savings, improved monitoring, unified experience

