package com.example.payments;

import java.math.BigDecimal;
import java.util.List;

/**
 * A plain-main demo so the Java side runs WITHOUT starting a Spring container
 * (the class is just `new`-ed directly; @Service only matters to a Spring context).
 * It exercises the exact arithmetic the Python port must reproduce, so the two
 * sides can be compared number-for-number.
 */
public class Demo {
    public static void main(String[] args) {
        // The trap case: 0.10 + 0.20. In binary float this is 0.30000000000000004.
        Money a = Money.of("0.10", "USD");
        Money b = Money.of("0.20", "USD");
        System.out.println("0.10 + 0.20 = " + a.add(b));            // -> 0.30 USD (exact)

        // Bankers' rounding: 2.005 at 2dp HALF_EVEN -> 2.00 (rounds to even), not 2.01.
        Money r = Money.of("2.005", "USD");
        System.out.println("round(2.005) = " + r);                  // -> 2.00 USD

        // JPY has 0 minor units: 199.7 -> 200 JPY.
        Money jpy = Money.of("199.7", "JPY");
        System.out.println("199.7 JPY    = " + jpy);                // -> 200 JPY

        // Order total: 3 x 19.99 USD + 21% tax.
        OrderTotalService svc = new OrderTotalService();
        Money total = svc.total(
                List.of(new OrderTotalService.LineItem(Money.of("19.99", "USD"), 3)),
                new BigDecimal("0.21"));
        System.out.println("3x19.99 +21% = " + total);              // -> 72.56 USD

        // Currency mismatch is a hard error, never a silent wrong total.
        try {
            Money.of("1.00", "USD").add(Money.of("1.00", "EUR"));
        } catch (IllegalArgumentException ex) {
            System.out.println("mismatch     = " + ex.getMessage());
        }
    }
}
