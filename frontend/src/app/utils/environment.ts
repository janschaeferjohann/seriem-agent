/**
 * Environment utilities for detecting runtime context.
 */

/**
 * Check if the app is running inside Electron.
 * This is true when the preload script has exposed electronAPI.
 */
export const isElectron = typeof window !== 'undefined' && !!window.electronAPI;

/**
 * Check if the app is running in development mode.
 * In Angular, this is determined by the build configuration.
 */
export const isDevelopment = !!(window as any).ng?.probe;

