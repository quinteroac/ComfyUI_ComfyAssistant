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

// Wrapper component with i18n
function AssistantWrapper() {
  useTranslation()
  return <App />
}

// Mount React app into a container element
function mountReact(container: HTMLElement): ReactDOM.Root {
  const root = ReactDOM.createRoot(container)
  root.render(
    <React.StrictMode>
      <TooltipProvider>
        <Suspense fallback={<div>Loading...</div>}>
          <AssistantWrapper />
        </Suspense>
      </TooltipProvider>
    </React.StrictMode>
  )
  return root
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

    let reactRoot: ReactDOM.Root | null = null

    // Register extension with bottom panel tab
    window.app.registerExtension({
      name: 'ComfyUI_ComfyAssistant',
      bottomPanelTabs: [
        {
          id: 'comfyui-assistant',
          title: 'Assistant',
          type: 'custom' as const,
          render: (element: HTMLElement) => {
            console.log('Rendering ComfyUI Assistant (bottom panel)')
            element.style.cssText =
              'height:100%;min-height:0;overflow:hidden;display:flex;flex-direction:column'
            const container = document.createElement('div')
            container.id = 'comfyui-assistant-root'
            container.style.cssText =
              'height:100%;min-height:0;overflow:hidden;display:flex;flex-direction:column'
            element.appendChild(container)
            reactRoot = mountReact(container)
          },
          destroy: () => {
            console.log('Destroying ComfyUI Assistant (bottom panel)')
            reactRoot?.unmount()
            reactRoot = null
          }
        }
      ]
    })

    // Fallback: if bottomPanelTabs isn't supported, register as sidebar tab
    // Uncomment if needed for older ComfyUI versions:
    // window.app.extensionManager.registerSidebarTab({
    //   id: 'comfyui-assistant-sidebar',
    //   icon: 'pi pi-comments',
    //   title: 'Assistant',
    //   tooltip: 'ComfyUI Assistant',
    //   type: 'custom' as const,
    //   render: (element: HTMLElement) => {
    //     const container = document.createElement('div')
    //     container.id = 'comfyui-assistant-root'
    //     container.style.cssText =
    //       'height:100%;min-height:0;overflow:hidden;display:flex;flex-direction:column'
    //     element.appendChild(container)
    //     reactRoot = mountReact(container)
    //   }
    // })

    console.log('ComfyUI Assistant initialized successfully')
  } catch (error) {
    console.error('Failed to initialize ComfyUI Assistant:', error)
  }
}

// Start initialization
void initializeExtension()
