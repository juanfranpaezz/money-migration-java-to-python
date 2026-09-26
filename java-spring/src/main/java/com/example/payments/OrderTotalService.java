package com.example.payments;

import java.math.BigDecimal;
import java.util.List;
import org.springframework.stereotype.Service;

/**
 * A small Spring service that totals an order: sum(line items) + tax.
 *
 * <p>This is the classic Spring shape we are migrating: a {@code @Service} bean with
 * a single pure method, injected into a controller. It does all money arithmetic
 * through {@link Money} so the rounding/currency rules live in one place.
 */
@Service
public class OrderTotalService {

    /** One order line: a unit price and an integer quantity. */
    public record LineItem(Money unitPrice, long quantity) {}

    /**
     * Total an order: subtotal = sum(unitPrice * quantity), then add tax = subtotal * taxRate.
     * All lines must share one currency (Money.add enforces this). The tax is rounded
     * HALF_EVEN to the currency scale by {@link Money#percentage}.
     *
     * @param lines   the order lines (at least one)
     * @param taxRate the tax rate as a fraction, e.g. 0.21 for 21%
     * @return the grand total as Money
     */
    public Money total(List<LineItem> lines, BigDecimal taxRate) {
        if (lines == null || lines.isEmpty()) {
            throw new IllegalArgumentException("an order needs at least one line");
        }
        Money subtotal = null;
        for (LineItem line : lines) {
            Money lineTotal = line.unitPrice().multiply(line.quantity());
            subtotal = (subtotal == null) ? lineTotal : subtotal.add(lineTotal);
        }
        Money tax = subtotal.percentage(taxRate);
        return subtotal.add(tax);
    }
}
