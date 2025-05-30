import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "../contexts/AuthContext";
import styles from "./Login.styles";

const Login = () => {
  const { login } = useAuth();

  const handleSuccess = (credentialResponse) => {
    login(credentialResponse.credential);
  };

  const handleError = () => {
    console.error("Login Failed");
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Welcome to Metropole.AI</h1>
        <p style={styles.subtitle}>Please sign in to continue</p>
        <div style={styles.loginButton}>
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={handleError}
            useOneTap
          />
        </div>
      </div>
    </div>
  );
};

export default Login;
