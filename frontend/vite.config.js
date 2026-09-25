import { resolve } from 'path';
import fs from 'fs';

export default {
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        desk: resolve(__dirname, 'desk.html'),
        auth: resolve(__dirname, 'auth.html'),
      },
    },
  },
  plugins: [
    {
      name: 'copy-static-assets',
      closeBundle() {
        const copyDir = (src, dest) => {
          if (!fs.existsSync(src)) return;
          fs.mkdirSync(dest, { recursive: true });
          for (const item of fs.readdirSync(src, { withFileTypes: true })) {
            const srcPath = resolve(src, item.name);
            const destPath = resolve(dest, item.name);
            if (item.isDirectory()) {
              copyDir(srcPath, destPath);
            } else {
              fs.copyFileSync(srcPath, destPath);
            }
          }
        };
        copyDir(resolve(__dirname, 'css'), resolve(__dirname, 'dist/css'));
        copyDir(resolve(__dirname, 'js'), resolve(__dirname, 'dist/js'));
        copyDir(resolve(__dirname, 'src'), resolve(__dirname, 'dist/src'));
      }
    }
  ]
};
