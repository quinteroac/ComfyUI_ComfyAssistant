import { ComfyApp } from '@comfyorg/comfyui-frontend-types'
import React, { Suspense } from 'react'
import ReactDOM from 'react-dom/client'
import { useTranslation } from 'react-i18next'

import { TooltipProvider } from '@/components/ui/tooltip'

import './index.css'
import './utils/i18n'

// Declare global ComfyUI objects
declare global {
  interface Window {
    app?: ComfyApp
  }
}

// Lazy load the App component for better performance
const App = React.lazy(() => import('./App'))

// Function to wait for document and app to be ready
function waitForInit(): Promise<void> {
  return new Promise((resolve) => {
    // Check if document is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', checkApp)
    } else {
      checkApp()
    }

    // Check if app is available
    function checkApp() {
      if (window.app) {
        resolve()
      } else {
        // Poll for app availability
        const interval = setInterval(() => {
          if (window.app) {
            console.log('App initialized')
            clearInterval(interval)
            resolve()
          }
        }, 50)

        // Set timeout to avoid infinite polling
        setTimeout(() => {
          clearInterval(interval)
          console.error('Timeout waiting for app to initialize')
          resolve() // Continue anyway to avoid blocking
        }, 5000)
      }
    }
  })
}

// Initialize the extension once everything is ready
async function initializeExtension(): Promise<void> {
  try {
    // Wait for document and ComfyUI app
    await waitForInit()
    console.log('App:', window.app)

    if (!window.app) {
      console.error('ComfyUI app not available')
      return
    }

    // Create a function component with i18n for translation
    function SidebarWrapper() {
      // Using useTranslation hook to initialize i18n context
      useTranslation()
      return <App />
    }

    // Register the sidebar tab using ComfyUI's extension API
    const sidebarTab = {
      id: 'comfyui-assistant-sidebar',
      icon: 'pi pi-comments', // Using PrimeVue icon for chat
      title: 'Assistant',
      tooltip: 'ComfyUI Assistant',
      type: 'custom' as const,
      render: (element: HTMLElement) => {
        console.log('Rendering ComfyUI Assistant')
        // Create a container for our React app
        const container = document.createElement('div')
        container.id = 'comfyui-assistant-root'
        container.style.cssText =
          'height:100%;min-height:0;overflow:hidden;display:flex;flex-direction:column'
        element.appendChild(container)

        // Mount the React app to the container
        ReactDOM.createRoot(container).render(
          <React.StrictMode>
            <TooltipProvider>
              <Suspense fallback={<div>Loading...</div>}>
                <SidebarWrapper />
              </Suspense>
            </TooltipProvider>
          </React.StrictMode>
        )
      }
    }

    window.app.extensionManager.registerSidebarTab(sidebarTab)

    // Register extension with about page badges
    window.app.registerExtension({
      name: 'ComfyUI_ComfyAssistant'
    })

    console.log('ComfyUI Assistant initialized successfully')
  } catch (error) {
    console.error('Failed to initialize React Example Extension:', error)
  }
}

// Start initialization
void initializeExtension()
