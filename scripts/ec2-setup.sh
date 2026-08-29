#!/usr/bin/env bash
# ==============================================================================
# BABYCARE AI - AWS EC2 AUTOMATED SERVER BOOTSTRAP SCRIPT
# ==============================================================================
# Kịch bản tự động hóa cài đặt & cấu hình môi trường máy chủ AWS EC2 (Ubuntu LTS)
# Hỗ trợ: Docker Engine, Docker Compose, Swap Memory, UFW Firewall, NVIDIA GPU
#
# Cách sử dụng trên server EC2:
#   chmod +x scripts/ec2-setup.sh
#   sudo ./scripts/ec2-setup.sh
# ==============================================================================

set -eo pipefail

# Màu sắc thông báo
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_step() {
    echo -e "\n${CYAN}================================================================${NC}"
    echo -e "${CYAN}[Step $1] $2${NC}"
    echo -e "${CYAN}================================================================${NC}"
}

log_success() {
    echo -e "  ${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "  ${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "  ${RED}❌ $1${NC}"
    exit 1
}

# Kiểm tra quyền root
if [ "$EUID" -ne 0 ]; then
    log_error "Vui lòng chạy kịch bản này với quyền root: sudo ./scripts/ec2-setup.sh"
fi

REAL_USER="${SUDO_USER:-$USER}"

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}  🚀 BABYCARE AI - KHỞI TẠO HẠ TẦNG MÁY CHỦ AWS EC2${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e "  • Hệ điều hành    : $(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2)"
echo -e "  • Người dùng triển khai: ${REAL_USER}"

# ------------------------------------------------------------------------------
# STEP 1: CẬP NHẬT HỆ THỐNG & CÀI ĐẶT CÔNG CỤ CƠ BẢN
# ------------------------------------------------------------------------------
log_step "1/6" "Cập nhật hệ điều hành và cài đặt gói tiện ích thiết yếu..."

export DEBIAN_FRONTEND=noninteractive
apt-get update -y && apt-get upgrade -y

apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    make \
    htop \
    ufw \
    net-tools \
    unzip \
    jq \
    software-properties-common

log_success "Hệ thống đã được cập nhật và cài đặt công cụ cần thiết."

# ------------------------------------------------------------------------------
# STEP 2: THIẾT LẬP BỘ NHỚ ẢO (4GB SWAP MEMORY)
# ------------------------------------------------------------------------------
log_step "2/6" "Thiết lập 4GB Swap Memory (Ngăn ngừa tràn RAM khi nạp AI Models)..."

if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=4096
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
    log_success "Đã tạo và kích hoạt 4GB Swap file thành công."
else
    log_success "Swap file đã tồn tại, bỏ qua bước tạo mới."
fi

# Tối ưu hóa giới hạn mmap cho AI Vector Search & Elasticsearch/FAISS
sysctl -w vm.max_map_count=262144
if ! grep -q "vm.max_map_count=262144" /etc/sysctl.conf; then
    echo 'vm.max_map_count=262144' >> /etc/sysctl.conf
fi

# ------------------------------------------------------------------------------
# STEP 3: CÀI ĐẶT DOCKER ENGINE & DOCKER COMPOSE V2 CHÍNH HÃNG
# ------------------------------------------------------------------------------
log_step "3/6" "Cài đặt Docker Engine & Docker Compose V2..."

if ! command -v docker &> /dev/null; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    systemctl enable docker
    systemctl start docker
    log_success "Cài đặt Docker Engine thành công: $(docker --version)"
else
    log_success "Docker đã được cài đặt sẵn: $(docker --version)"
fi

# Cấp quyền cho user không cần sudo khi gọi docker
usermod -aG docker "$REAL_USER"
log_success "Đã thêm người dùng '${REAL_USER}' vào nhóm 'docker'."

# ------------------------------------------------------------------------------
# STEP 4: CẤU HÌNH TĂNG TỐC NVIDIA GPU (NẾU PHÁT HIỆN CARD ĐỒ HỌA)
# ------------------------------------------------------------------------------
log_step "4/6" "Kiểm tra phần cứng NVIDIA GPU..."

if lspci 2>/dev/null | grep -qi nvidia; then
    log_warning "Phát hiện card đồ họa NVIDIA. Đang cài đặt NVIDIA Container Toolkit..."
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg --yes
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
      sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
      tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    apt-get update -y
    apt-get install -y nvidia-container-toolkit
    nvidia-ctk runtime configure --runtime=docker
    systemctl restart docker
    log_success "NVIDIA Container Toolkit đã sẵn sàng cho AI Acceleration."
else
    log_success "Máy chủ CPU chuẩn (Không phát hiện GPU chuyên dụng)."
fi

# ------------------------------------------------------------------------------
# STEP 5: THIẾT LẬP TƯỜNG LỬA BẢO MẬT (UFW FIREWALL)
# ------------------------------------------------------------------------------
log_step "5/6" "Thiết lập quy tắc Tường lửa UFW..."

ufw default deny incoming
ufw default allow outgoing

# Mở các cổng dịch vụ cần thiết
ufw allow 22/tcp comment 'SSH Remote Access'
ufw allow 80/tcp comment 'HTTP Web Gateway'
ufw allow 443/tcp comment 'HTTPS Secure Gateway'

# Kích hoạt UFW tự động
echo "y" | ufw enable
log_success "Tường lửa UFW đã kích hoạt: Cho phép 22 (SSH), 80 (HTTP), 443 (HTTPS)."

# ------------------------------------------------------------------------------
# STEP 6: HOÀN TẤT & HƯỚNG DẪN BƯỚC TIẾP THEO
# ------------------------------------------------------------------------------
log_step "6/6" "Hoàn tất Khởi tạo Máy chủ EC2"

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}  🎉 KHỞI TẠO MÁY CHỦ THÀNH CÔNG! HẠ TẦNG ĐÃ SẴN SÀNG.${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e "  👉 Các bước tiếp theo để chạy dự án BabyCare AI:"
echo -e ""
echo -e "  1. Áp dụng quyền Docker (không cần sudo):"
echo -e "     ${CYAN}newgrp docker${NC} hoặc đăng nhập lại SSH"
echo -e ""
echo -e "  2. Nạp cấu hình môi trường Production:"
echo -e "     ${CYAN}make env-prod${NC} (Điền các API keys thật vào file .env.production)"
echo -e ""
echo -e "  3. Khởi chạy toàn bộ hệ thống bằng Docker Compose:"
echo -e "     ${CYAN}make docker-prod${NC}"
echo -e ""
echo -e "  4. Kiểm tra sức khỏe toàn diện hệ thống:"
echo -e "     ${CYAN}make health-check${NC}"
echo -e "${GREEN}================================================================${NC}\n"
