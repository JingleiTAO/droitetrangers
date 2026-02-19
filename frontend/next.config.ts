import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  eslint: {
    // 允许在生产构建中存在 ESLint 错误
    ignoreDuringBuilds: true,
  },
  typescript: {
    // 允许在生产构建中存在类型错误
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
