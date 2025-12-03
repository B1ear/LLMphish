import { createRouter, createWebHistory } from "vue-router";
import Dashboard from "../views/Dashboard.vue";
import UploadView from "../views/UploadView.vue";
import FeatureView from "../views/FeatureView.vue";
import DetectionView from "../views/DetectionView.vue";
import ResultView from "../views/ResultView.vue";

const routes = [
  { path: "/", name: "dashboard", component: Dashboard },
  { path: "/upload", name: "upload", component: UploadView },
  { path: "/features/:emailId", name: "features", component: FeatureView, props: true },
  { path: "/detection/:emailId", name: "detection", component: DetectionView, props: true },
  { path: "/results/:emailId", name: "results", component: ResultView, props: true }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;


