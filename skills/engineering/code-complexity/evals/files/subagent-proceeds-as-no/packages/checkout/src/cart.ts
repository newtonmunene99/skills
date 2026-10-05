export interface Item {
  id: string;
  qty: number;
  price: number;
}

export interface CartState {
  items: Item[];
  coupon: string | null;
  shipping: string | null;
  status: "idle" | "pending" | "failed" | "done";
  error: string | null;
  orderId: string | null;
}

export const initialState: CartState = {
  items: [],
  coupon: null,
  shipping: null,
  status: "idle",
  error: null,
  orderId: null,
};

export type Action =
  | { type: "add"; item: Item }
  | { type: "remove"; id: string }
  | { type: "clear" }
  | { type: "setQty"; id: string; qty: number }
  | { type: "applyCoupon"; code: string }
  | { type: "removeCoupon" }
  | { type: "setShipping"; method: string }
  | { type: "beginCheckout" }
  | { type: "checkoutFailed"; error: string }
  | { type: "checkoutSucceeded"; orderId: string }
  | { type: "retry" }
  | { type: "reset" };

export function cartReducer(state: CartState, action: Action): CartState {
  switch (action.type) {
    case "add":
      return { ...state, items: [...state.items, action.item] };
    case "remove":
      return { ...state, items: state.items.filter((i) => i.id !== action.id) };
    case "clear":
      return { ...state, items: [] };
    case "setQty":
      return {
        ...state,
        items: state.items.map((i) => (i.id === action.id ? { ...i, qty: action.qty } : i)),
      };
    case "applyCoupon":
      return { ...state, coupon: action.code };
    case "removeCoupon":
      return { ...state, coupon: null };
    case "setShipping":
      return { ...state, shipping: action.method };
    case "beginCheckout":
      return { ...state, status: "pending", error: null };
    case "checkoutFailed":
      return { ...state, status: "failed", error: action.error };
    case "checkoutSucceeded":
      return { ...state, status: "done", orderId: action.orderId };
    case "retry":
      return { ...state, status: "idle", error: null };
    case "reset":
      return initialState;
  }
}
