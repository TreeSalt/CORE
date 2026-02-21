#include <stdio.h>

/*
 * Item 21: Bit-Perfect Physics Mirror (C Core).
 * Deterministic calculation of account equity and position state.
 */

typedef struct {
  double cash;
  double qty;
  double last_price;
} AccountState;

void update_account(AccountState *state, double price, double qty_delta,
                    double commission) {
  if (qty_delta != 0) {
    state->cash -= (qty_delta * price) + commission;
    state->qty += qty_delta;
  }
  state->last_price = price;
}

double get_equity(const AccountState *state) {
  return state->cash + (state->qty * state->last_price);
}
