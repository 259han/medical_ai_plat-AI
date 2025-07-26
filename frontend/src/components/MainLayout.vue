<template>
  <el-container>
    <el-header class="header">
      <div class="header-left">
        <el-button class="menu-btn hidden-desktop" icon="Menu" @click="drawerVisible = true" circle></el-button>
        <h2>
          <slot name="header-icon"></slot>
          <slot name="header-title">医疗AI平台</slot>
        </h2>
      </div>
      <div class="header-right">
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-avatar :size="32">
              {{ user?.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <span class="username">{{ user?.username }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人资料</el-dropdown-item>
              <el-dropdown-item command="history">历史记录</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    <el-container>
      <el-aside width="250px" class="sidebar hidden-mobile">
        <el-menu :default-active="activeMenu" class="sidebar-menu" router>
          <el-menu-item index="/dashboard">
            <el-icon><Monitor /></el-icon>
            <span>仪表板</span>
          </el-menu-item>
          <el-menu-item index="/medical-qa">
            <el-icon><ChatDotRound /></el-icon>
            <span>医疗问答</span>
          </el-menu-item>
          <el-menu-item index="/heart-disease">
            <el-icon><TrendCharts /></el-icon>
            <span>心脏病预测</span>
          </el-menu-item>
          <el-menu-item index="/tumor">
            <span>肿瘤分类</span>
          </el-menu-item>
          <el-menu-item index="/diabetes">
            <el-icon><TrendCharts /></el-icon>
            <span>糖尿病评估</span>
          </el-menu-item>
          <el-menu-item index="/chest-xray">
            <el-icon><Camera /></el-icon>
            <span>胸部X光预测</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="main-content">
        <slot />
      </el-main>
    </el-container>
    <!-- 移动端抽屉菜单 -->
    <el-drawer v-model="drawerVisible" direction="ltr" size="70vw" class="mobile-drawer" :with-header="false">
      <el-menu :default-active="activeMenu" class="sidebar-menu" router @select="drawerVisible = false">
        <el-menu-item index="/dashboard">
          <el-icon><Monitor /></el-icon>
          <span>仪表板</span>
        </el-menu-item>
        <el-menu-item index="/medical-qa">
          <el-icon><ChatDotRound /></el-icon>
          <span>医疗问答</span>
        </el-menu-item>
        <el-menu-item index="/heart-disease">
          <el-icon><TrendCharts /></el-icon>
          <span>心脏病预测</span>
        </el-menu-item>
        <el-menu-item index="/tumor">
          <span>肿瘤分类</span>
        </el-menu-item>
        <el-menu-item index="/diabetes">
          <el-icon><TrendCharts /></el-icon>
          <span>糖尿病评估</span>
        </el-menu-item>
        <el-menu-item index="/chest-xray">
          <el-icon><Camera /></el-icon>
          <span>胸部X光预测</span>
        </el-menu-item>
      </el-menu>
    </el-drawer>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { Monitor, ChatDotRound, TrendCharts, ArrowDown, Camera, UserFilled, Menu } from '@element-plus/icons-vue'

const props = defineProps({
  activeMenu: {
    type: String,
    default: ''
  }
})

const router = useRouter()
const authStore = useAuthStore()
const user = computed(() => authStore.user)
const drawerVisible = ref(false)

const handleCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'history':
      router.push('/history')
      break
    case 'logout':
      authStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
      break
  }
}
</script>

<style scoped>
.header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.menu-btn {
  margin-right: 10px;
}
@media (min-width: 769px) {
  .menu-btn {
    display: none !important;
  }
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: background-color 0.3s;
}
.user-info:hover {
  background-color: #f5f7fa;
}
.username {
  font-weight: 500;
}
.sidebar {
  background: white;
  border-right: 1px solid #e4e7ed;
}
.sidebar-menu {
  border-right: none;
}
.main-content {
  background: #f5f7fa;
  padding: 20px;
}
.mobile-drawer {
  z-index: 3000;
}
</style> 