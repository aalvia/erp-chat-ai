import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { useAuth } from "./contexts/AuthContext";
import { AuditPage, SettingsPage } from "./pages/AuditSettingsPages";
import { CustomerDetailPage, CustomerFormPage, CustomersPage } from "./pages/CustomerPages";
import { DashboardPage } from "./pages/DashboardPage";
import { InventoryPage, MovementsPage } from "./pages/InventoryPages";
import { LoginPage } from "./pages/LoginPage";
import { ProductFormPage, ProductsPage } from "./pages/ProductPages";
import { SaleDetailPage, SaleFormPage, SalesPage } from "./pages/SalesPages";
import { RolesPage, UserFormPage, UsersPage } from "./pages/UsersPages";

function Protected({ children, anyOf }: { children: React.ReactNode; anyOf?: string[] }) {
  const { user, loading, can } = useAuth();
  if (loading) return <p className="content">Cargando sesión...</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (anyOf && !can(...anyOf)) return <div className="content"><div className="card">No tienes permiso para ver esta pantalla.</div></div>;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<Protected><AppLayout /></Protected>}>
        <Route path="/" element={<Protected anyOf={["dashboard.read"]}><DashboardPage /></Protected>} />
        <Route path="/admin/users" element={<Protected anyOf={["users.read"]}><UsersPage /></Protected>} />
        <Route path="/admin/users/new" element={<Protected anyOf={["users.write"]}><UserFormPage /></Protected>} />
        <Route path="/admin/users/:id" element={<Protected anyOf={["users.write"]}><UserFormPage /></Protected>} />
        <Route path="/admin/roles" element={<Protected anyOf={["roles.read"]}><RolesPage /></Protected>} />
        <Route path="/customers" element={<Protected anyOf={["customers.read"]}><CustomersPage /></Protected>} />
        <Route path="/customers/new" element={<Protected anyOf={["customers.write"]}><CustomerFormPage /></Protected>} />
        <Route path="/customers/:id" element={<Protected anyOf={["customers.read"]}><CustomerDetailPage /></Protected>} />
        <Route path="/products" element={<Protected anyOf={["products.read"]}><ProductsPage /></Protected>} />
        <Route path="/products/new" element={<Protected anyOf={["products.write"]}><ProductFormPage /></Protected>} />
        <Route path="/products/:id" element={<Protected anyOf={["products.read"]}><ProductFormPage /></Protected>} />
        <Route path="/inventory" element={<Protected anyOf={["inventory.read"]}><InventoryPage /></Protected>} />
        <Route path="/inventory/movements" element={<Protected anyOf={["inventory.read"]}><MovementsPage /></Protected>} />
        <Route path="/sales" element={<Protected anyOf={["sales.read_own", "sales.read_all", "sales.create"]}><SalesPage /></Protected>} />
        <Route path="/sales/new" element={<Protected anyOf={["sales.create"]}><SaleFormPage /></Protected>} />
        <Route path="/sales/:id" element={<Protected anyOf={["sales.read_own", "sales.read_all", "sales.create"]}><SaleDetailPage /></Protected>} />
        <Route path="/audit" element={<Protected anyOf={["audit.read"]}><AuditPage /></Protected>} />
        <Route path="/settings" element={<Protected anyOf={["settings.write"]}><SettingsPage /></Protected>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
