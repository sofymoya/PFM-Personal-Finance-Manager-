import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import vector0 from '../assets/vector-0.svg';

interface RegisterProps {
  onRegister: (name: string, email: string, password: string) => Promise<{ success: boolean; error?: string }>;
}

const Register: React.FC<RegisterProps> = ({ onRegister }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      setLoading(false);
      return;
    }
    const result = await onRegister(name, email, password);
    if (!result.success) {
      setError(result.error || 'Error signing up');
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col items-start relative bg-white min-h-screen">
      <div className="flex flex-col min-h-[800px] items-start relative self-stretch w-full flex-[0_0_auto] bg-white">
        <div className="flex flex-col items-start relative self-stretch w-full flex-[0_0_auto]">
          <div className="items-center justify-around px-10 py-3 flex-[0_0_auto] border-b border-[#e5e8ea] flex relative self-stretch w-full">
            <div className="inline-flex items-center gap-4 relative flex-[0_0_auto]">
              <div className="inline-flex flex-col items-start relative flex-[0_0_auto]">
                <div className="w-4 relative flex-1 grow">
                  <img className="absolute w-[13px] h-[13px] top-px left-px" alt="Vector" src={vector0} />
                </div>
              </div>
              <div className="inline-flex flex-col items-start relative flex-[0_0_auto]">
                <div className="relative self-stretch mt-[-1.00px] font-bold text-[#111416] text-lg tracking-[0] leading-[23px] whitespace-nowrap">
                  FinTrack
                </div>
              </div>
            </div>
          </div>

          <div className="items-start justify-center px-4 md:px-40 py-5 flex-1 grow flex relative self-stretch w-full">
            <div className="flex flex-col max-w-md w-full items-center px-0 py-5 relative flex-[0_0_auto] mb-[-1.00px] mx-auto">
              <div className="flex flex-col items-center pt-5 pb-3 px-4 self-stretch w-full relative flex-[0_0_auto]">
                <div className="relative self-stretch mt-[-1.00px] font-bold text-[#111416] text-[28px] text-center tracking-[0] leading-[35px]">
                  Create your account
                </div>
              </div>
              {error && (
                <div className="flex max-w-[480px] items-center justify-center gap-2.5 px-4 py-3 relative w-full">
                  <div className="flex flex-col w-full items-start relative">
                    <div className="flex items-center p-4 relative self-stretch w-full bg-red-50 border border-red-200 rounded-xl">
                      <div className="relative w-fit font-normal text-red-600 text-sm">
                        {error}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <form onSubmit={handleSubmit} className="w-full max-w-md flex flex-col gap-4">
                <div className="flex flex-col w-full">
                  <label className="font-medium text-[#111416] text-base mb-1">Full Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="h-14 p-[15px] bg-white rounded-xl border border-solid border-[#dde0e2] w-full font-normal text-[#111416] text-base placeholder:text-[#667782]"
                    placeholder="Enter your full name"
                  />
                </div>
                <div className="flex flex-col w-full">
                  <label className="font-medium text-[#111416] text-base mb-1">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="h-14 p-[15px] bg-white rounded-xl border border-solid border-[#dde0e2] w-full font-normal text-[#111416] text-base placeholder:text-[#667782]"
                    placeholder="Enter your email"
                  />
                </div>
                <div className="flex flex-col w-full">
                  <label className="font-medium text-[#111416] text-base mb-1">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="h-14 p-[15px] bg-white rounded-xl border border-solid border-[#dde0e2] w-full font-normal text-[#111416] text-base placeholder:text-[#667782]"
                    placeholder="Enter your password"
                  />
                </div>
                <div className="flex flex-col w-full">
                  <label className="font-medium text-[#111416] text-base mb-1">Confirm Password</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="h-14 p-[15px] bg-white rounded-xl border border-solid border-[#dde0e2] w-full font-normal text-[#111416] text-base placeholder:text-[#667782]"
                    placeholder="Confirm your password"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full h-10 items-center justify-center px-4 py-0 bg-[#338ec9] rounded-[20px] text-white font-bold text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#256fa1] transition-colors mt-2"
                >
                  {loading ? 'Signing up...' : 'Sign Up'}
                </button>
              </form>
              <div className="flex flex-col items-center pt-1 pb-3 px-4 self-stretch w-full relative flex-[0_0_auto]">
                <div className="relative self-stretch mt-[-1.00px] font-normal text-[#667782] text-sm text-center tracking-[0] leading-[21px]">
                  Already have an account?
                </div>
              </div>
              <div className="flex flex-col items-center pt-1 pb-3 px-4 self-stretch w-full relative flex-[0_0_auto]">
                <Link to="/login" className="relative self-stretch mt-[-1.00px] font-normal text-[#667782] text-sm text-center tracking-[0] leading-[21px] hover:text-[#338ec9] transition-colors">
                  Log In
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register; 