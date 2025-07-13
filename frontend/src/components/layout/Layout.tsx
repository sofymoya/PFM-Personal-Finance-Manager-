import React from 'react';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-white">
      <main className="flex flex-col items-center justify-center min-h-screen w-full">
        <div className="w-full">{children}</div>
      </main>
    </div>
  );
};

export default Layout; 