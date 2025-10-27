import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Header from './components/Header'
import Home from './components/Home'
import LoginForm from './components/LoginForm'
import RegisterForm from './components/RegisterForm'
import Dashboard from './components/Dashboard'
import Profile from './components/Profile'
import ProtectedRoute from './components/ProtectedRoute'
import PlaceholderPage from './components/PlaceholderPage'
import FloatingButtons from './components/FloatingButtons'
import ManageAccounts from './components/ManageAccounts'
import ChangePassword from './components/ChangePassword'
import SecuritySettings from './components/SecuritySettings'
import TransferSystem from './components/TransferSystem'
import TransactionHistory from './components/TransactionHistory'

// Import all page components
import Accounts from './pages/Accounts'
import Payments from './pages/Payments'
import Shop from './pages/Shop'
import Investments from './pages/Investments'
import Loans from './pages/Loans'
import Cards from './pages/Cards'
import Insurance from './pages/Insurance'
import Services from './pages/Services'

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Header />
          <FloatingButtons />
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<LoginForm />} />
            <Route path="/register" element={<RegisterForm />} />
            
            {/* Protected Routes */}
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } 
            />
            
            {/* Account Management Routes */}
            <Route 
              path="/accounts/*" 
              element={
                <ProtectedRoute>
                  <Accounts />
                </ProtectedRoute>
              } 
            />
            
       {/* Payment Routes */}
       <Route 
         path="/payments/transfer" 
         element={
           <ProtectedRoute>
             <TransferSystem />
           </ProtectedRoute>
         } 
       />
       <Route 
         path="/payments/beneficiaries" 
         element={
           <ProtectedRoute>
             <TransferSystem />
           </ProtectedRoute>
         } 
       />
       <Route 
         path="/payments/history" 
         element={
           <ProtectedRoute>
             <TransactionHistory />
           </ProtectedRoute>
         } 
       />
            <Route 
              path="/payments/*" 
              element={
                <ProtectedRoute>
                  <Payments />
                </ProtectedRoute>
              } 
            />
            
            {/* Shop Routes */}
            <Route 
              path="/shop" 
              element={
                <ProtectedRoute>
                  <Shop />
                </ProtectedRoute>
              } 
            />
            
            {/* Investment Routes */}
            <Route 
              path="/investments/*" 
              element={
                <ProtectedRoute>
                  <Investments />
                </ProtectedRoute>
              } 
            />
            
            {/* Loan Routes */}
            <Route 
              path="/loans/*" 
              element={
                <ProtectedRoute>
                  <Loans />
                </ProtectedRoute>
              } 
            />
            
            {/* Card Routes */}
            <Route 
              path="/cards/*" 
              element={
                <ProtectedRoute>
                  <Cards />
                </ProtectedRoute>
              } 
            />
            
            {/* Insurance Routes */}
            <Route 
              path="/insurance/*" 
              element={
                <ProtectedRoute>
                  <Insurance />
                </ProtectedRoute>
              } 
            />
            
            {/* Service Routes */}
            <Route 
              path="/services/*" 
              element={
                <ProtectedRoute>
                  <Services />
                </ProtectedRoute>
              } 
            />
            
            {/* Profile Routes */}
            <Route 
              path="/profile/update" 
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/profile/manage-accounts" 
              element={
                <ProtectedRoute>
                  <ManageAccounts />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/profile/change-password" 
              element={
                <ProtectedRoute>
                  <ChangePassword />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/profile/security" 
              element={
                <ProtectedRoute>
                  <SecuritySettings />
                </ProtectedRoute>
              } 
            />
            
            {/* Catch-all route for any unmatched paths */}
            <Route 
              path="*" 
              element={
                <PlaceholderPage 
                  title="Page Not Found"
                  description="The page you're looking for doesn't exist."
                  icon="❌"
                />
              } 
            />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App
