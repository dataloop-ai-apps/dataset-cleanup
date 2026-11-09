// @ts-nocheck

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import viteBasicSslPlugin from '@vitejs/plugin-basic-ssl'

// https://vitejs.dev/config/
export default defineConfig(({ command }) => ({
    build: {
        outDir: 'panels/cleanup'
    },
    // Built panel is served by piper under /api/v1/apps/<name>/panels/cleanup/, so assets must be relative.
    base: command === 'build' ? './' : '/cleanup',
    server: {
        host: '0.0.0.0',
        https: false,
        port: 8084
    },
    optimizeDeps: {
        include: [
            'lodash',
            '@dataloop-ai/components',
            'flat',
            'highlight.js',
            'sortablejs',
            '@dataloop-ai/jssdk',
            'tokenizr'
        ],
        exclude: ['node_modules', './node_modules', 'dist', './dist']
    },
    resolve: {
        alias: {
            '@': '/src'
        }
    },
    plugins: [viteBasicSslPlugin(), vue()],
    test: {
        environment: 'jsdom',
        setupFiles: ['tests/setup.js'],
        deps: {
            inline: ['vitest-canvas-mock']
        },
        coverage: {
            reporter: ['lcovonly', 'text']
        }
    }
}))
