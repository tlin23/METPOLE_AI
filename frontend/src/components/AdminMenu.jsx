import { useAuth } from "../contexts/AuthContext";
import styles from "./AdminMenu.styles";

const AdminMenu = () => {
  const { user } = useAuth();

  // Only show menu if user is admin
  if (!user?.is_admin) {
    return null;
  }

  return (
    <a
      href="/admin/db-query"
      target="_blank"
      rel="noopener noreferrer"
      style={styles.menuItem}
    >
      DB Query
    </a>
  );
};

export default AdminMenu;
