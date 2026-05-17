import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <h1>SafeSwing Trader</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
      </div>
      <p>
        Conservative Stock Market Monitoring & Swing Trade Assistant
      </p>
    </>
  )
}

export default App
