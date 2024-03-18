// const withBundleAnalyzer = require('@next/bundle-analyzer')({
//   enabled: process.env.ANALYZE === 'true',
//   // webpack: (config) => {
//   //   // See https://webpack.js.org/configuration/resolve/#resolvealias
//   //   config.resolve.alias = {
//   //       ...config.resolve.alias,
//   //       "sharp$": false,
//   //       "onnxruntime-node$": false,
//   //   }
//   //   config.externals = [...config.externals, "hnswlib-node"]
//   //   return config;
//   // },
//   experimental: {
//     serverComponentsExternalPackages: ['sharp', 'onnxruntime-node'],
//   },
//   output: 'standalone',
// })
// module.exports = withBundleAnalyzer({})

/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config) => {
      // Ignore node-specific modules when bundling for the browser
      // https://webpack.js.org/configuration/resolve/#resolvealias
      config.resolve.alias = {
          ...config.resolve.alias,
          "sharp$": false,
          "onnxruntime-node$": false,
      }
      return config;
  },
  output: "standalone",
};

module.exports = nextConfig;