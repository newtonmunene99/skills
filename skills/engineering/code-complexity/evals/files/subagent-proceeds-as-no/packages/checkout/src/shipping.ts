import type { Item } from "./cart";

export interface Rate {
  carrier: string;
  zone: string;
  maxGrams: number;
  price: number;
  expressOnly?: boolean;
}

export interface Address {
  country: string;
  zone?: string;
  poBox?: boolean;
}

export function quoteShipping(
  items: Item[],
  address: Address,
  rates: Rate[],
  express: boolean,
): Rate | null {
  let best: Rate | null = null;
  const grams = items.reduce((sum, i) => sum + i.qty * 500, 0);
  for (const rate of rates) {
    if (rate.zone === (address.zone ?? address.country)) {
      if (grams <= rate.maxGrams) {
        if (!express || rate.expressOnly) {
          if (address.poBox) {
            if (rate.carrier === "post") {
              if (!best || rate.price < best.price) {
                best = rate;
              }
            }
          } else if (!best || rate.price < best.price) {
            best = rate;
          }
        }
      }
    }
  }
  return best;
}
