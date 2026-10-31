import js from '@eslint/js';
import globals from 'globals';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';

/*
 * Lint config for the hand-written frontend source only.
 *
 * Why this exists: `vite build` bundles without checking identifier or hook
 * correctness, so a component used but never imported (bug: PredictionCard
 * rendered <Icon/> with no import) or a hook called conditionally ships
 * silently and only fails in the browser at runtime. `react/jsx-no-undef`
 * and `no-undef` catch the first class; `react-hooks/rules-of-hooks` catches
 * the second.
 *
 * Python/ML code is covered by pytest, not here. Build output and generated
 * caches are ignored.
 */
export default [
  {
    ignores: ['dist/**', 'node_modules/**', '.venv/**', 'trained_models/**'],
  },
  js.configs.recommended,
  {
    files: ['frontend/src/**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { ...globals.browser },
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    settings: { react: { version: 'detect' } },
    plugins: { react, 'react-hooks': reactHooks },
    rules: {
      ...react.configs.recommended.rules,
      // React 17+ uses the automatic JSX runtime via @vitejs/plugin-react,
      // so neither a `React` import nor `jsx-uses-react` is required.
      'react/react-in-jsx-scope': 'off',
      'react/jsx-uses-react': 'off',
      // No runtime prop validation in this project by design.
      'react/prop-types': 'off',
      // The jsx-* rules below are the ones that actually catch the class of
      // bug described above, so keep them explicit.
      'react/jsx-no-undef': 'error',
      'react/jsx-uses-vars': 'error',
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      'no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    },
  },
];
