import { resolve } from 'path';

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
};
