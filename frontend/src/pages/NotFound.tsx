import { useLocation } from "react-router-dom";
import { useEffect } from "react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted">
      <div className="text-center">
        <h1 className="mb-4 text-6xl font-extrabold text-primary">404</h1>
        <p className="mb-4 text-2xl font-bold text-muted-foreground">Oops! Something went wrong.</p>
        <p className="mb-8 text-lg text-muted-foreground">The page you are looking for does not exist or an error occurred.</p>
        <a href="/" className="inline-block px-6 py-3 rounded-lg bg-primary text-white font-semibold shadow hover:bg-primary/90 transition-colors">
          Return to Home
        </a>
      </div>
    </div>
  );
};

export default NotFound;
