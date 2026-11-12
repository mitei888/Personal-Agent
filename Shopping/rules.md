# Household shopping: shops & rules

Miranda stays logged in on all of these in Chrome. Fill the carts, then stop: she checks out and pays herself.

Carts are saved per browser, not per account: what we fill in the Mac's Chrome shows up EMPTY on her phone. With the cart summary, always send phone-ready links:
- WNP / Vetopia (Shopify): a cart permalink `https://<site>/cart/<variant_id>:<qty>,...` (get the ids from `/cart.js`; leave out auto-added free gifts).
- South Stream: no permalink, so send the product links with quantities.
- Two Chromes are connected to Claude on the Mac. Miranda checks out in HER Chrome and prefers opening the carts there and paying as the last step (Nov 2026). Before filling carts, check which browser is in use (`list_connected_browsers`) and, if unsure, ask her to select hers (`switch_browser`) so the carts land where she pays. Shopify links worked for her; South Stream must be filled in her browser or added by hand.
- Her Chrome is "Miranda's Mac mini HK". She pays through the cart links on her phone where possible; otherwise she remotes into the Mac mini, so fill non-link carts (South Stream) in that Chrome. South Stream asks for a delivery date first (profile details are prefilled; pick the date, then Confirm). Set qty by typing into the qty box then Tab; clicking the cart icon gives a harmless "system is busy" popup.

## Checkout: go as far as possible (Miranda, 11 Nov 2026)
Don't stop at the cart. Go through checkout and fill in everything you can (delivery address, date, contact details from her profile, discount code) up to the payment page. Per the ground rules in `CLAUDE.md`, show her a summary and get her "confirm" before the click that goes to payment (or places the order), then she pays.
After she pays, check the order total matches the cart total (on 11 Nov 2026 WNP charged $1,575 instead of the $1,373 cart price; the 11.11 discount didn't carry through the cart link).

South Stream payment shows cart total + 20% (e.g. $2,880 → $3,456, Nov 2026). Probably a card hold for weight variance, with the final invoice at actual weight; not confirmed by South Stream. Tell Miranda up front so it doesn't surprise her.

## Saved discount codes
| Shop | Code | Saved | Notes |
|---|---|---|---|
| iHerb | `HKWELL25` | 11 Nov 2026 | From Miranda. Try it at checkout and report whether it applied. |

## Discounts: check every time
Before handing over the carts, look for discounts on every site and report them:
- Site-wide sales and banners (11.11, Black Friday, etc.), the offers/promo page, and whether the discount is actually applied in the cart.
- Discount / promo codes: on the site (banners, offers page, member rewards) and a quick web search for current codes for that shop. Don't apply a code without telling her.

## Where to buy
| What | Shop | Site |
|---|---|---|
| Dog items (default) | Whiskers N Paws | wnp.com.hk (NOT whiskers-n-paws.com) |
| Dog shampoo | Vetopia | vetopia.com.hk |
| Dog dry food | epets | |
| Frozen meat & fish | South Stream Market | southstreammarket.com (cart: /en/Checkout/ShoppingCart; past orders: /en/Member/OrderHistory) |
| Pork belly (sometimes other meat) | Aussie Meat | aussiemeat.hk |

## Meat rules
- **Beef steaks:** NZ grass-fed, free-range, 8–10 oz (227–283 g).
- **Other meat:** free-range or grass-fed where possible.
- **Salmon & white fish:** ocean-caught (wild) if possible.
- **Chicken:** thighs. 1 piece = 1 thigh, so a pack of 4 counts as 4 pieces.

## Dogs: QQ & Snickers
- **QQ:** Malaseb Medicated Shampoo 1L (Vetopia).
- **Snickers' shampoo:** Aloveen Oatmeal 1L (Vetopia).
- **Dry food (epets):** Zignature, ONE single-protein bag (Pork, Beef or Lamb, any one of the three, not a mix), the 25 kg bag (Miranda's words, Nov 2026; Zignature bags are usually sold in lb, so check the size on epets).
- **Snickers:** PetCubes raw boxsets (WNP). She likes Lamb and Pork best; Kangaroo is OK. 1 box = 4 cubes (as she counts them). Count orders in cubes, so 30 cubes ≈ 7 boxes.
- **Paw cream:** Eye Envy On The Paw Therapy Balm 1.45 oz (WNP).
- **Toothpaste:** Petrodex. If the usual one is out of stock, get the cheaper option.
- **Ball for Snickers:** a big ball. None of WNP's balls were right (Nov 2026).

## Usual South Stream picks (Nov 2026)
- Steak: Hellaby Prime Steer Ribeye 250 g (NZ grass-fed, free range), HK$128.
- Salmon: Big Glory Bay King Salmon Portions 200 g. It's ocean-farmed; no wild salmon portions are sold.
- White fish: Hispamare Wild Caught Black Cod 150 g, or MSC Patagonian Toothfish 150 g.
- Shrimp: Vietnam Black Tiger Shrimp Meat 16/20, 500 g.
- Chicken: Bostock Brothers Organic Boneless Thighs Skin On 330 g (pieces per pack not stated).
