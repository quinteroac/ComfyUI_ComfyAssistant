// Import jest-dom additions (CommonJS for Jest compatibility with "type": "module")
require('@testing-library/jest-dom')

// Mock window.app for ComfyUI integration testing
global.window.app = {
  graph: {
    _nodes: []
  },
  api: {
    addEventListener: jest.fn(),
    removeEventListener: jest.fn()
  },
  canvas: {
    centerOnNode: jest.fn()
  }
}
