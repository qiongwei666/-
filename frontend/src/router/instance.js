// 保存路由实例，供 axios 拦截器等非组件模块使用。
// 单独抽成模块可以避免 request -> router -> views -> api -> request 的循环依赖。
let routerInstance = null

/** 注册路由实例 */
export function setRouterInstance(router) {
  routerInstance = router
}

/** 获取路由实例 */
export function getRouterInstance() {
  return routerInstance
}
