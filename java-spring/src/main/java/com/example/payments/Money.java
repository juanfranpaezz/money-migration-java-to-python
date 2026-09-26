package com.example.payments;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Currency;
import java.util.Objects;

/**
 * A money value-object: an immutable (amount, currency) pair with safe arithmetic.
 *
 * <p>This is the idiomatic Java/Spring shape for handling money in a fintech backend:
 * <ul>
 *   <li>The amount is a {@link BigDecimal}, never a {@code double} or {@code float}
 *       (binary floating point cannot represent decimal cents exactly, so it leaks
 *       rounding error into balances).</li>
 *   <li>The amount is normalised to the currency's minor-unit scale (e.g. 2 for USD,
 *       0 for JPY) using bankers' rounding ({@link RoundingMode#HALF_EVEN}), the
 *       conventional rounding mode for monetary settlement.</li>
 *   <li>Arithmetic is only defined between the SAME currency; mixing currencies is a
 *       programming error and throws, rather than silently producing a wrong total.</li>
 *   <li>The type is immutable: every operation returns a new {@code Money}.</li>
 * </ul>
 */
public final class Money {

    private final BigDecimal amount;
    private final Currency currency;

    private Money(BigDecimal amount, Currency currency) {
        this.amount = amount;
        this.currency = currency;
    }

    /**
     * Build a Money from a decimal amount and an ISO-4217 currency code.
     * The amount is rounded HALF_EVEN to the currency's default fraction digits.
     *
     * <p>The currency code is normalised to upper case first, so {@code "usd"} and
     * {@code "USD"} are accepted identically. This keeps the Java and Python ports
     * consistent: {@code Currency.getInstance} is case-sensitive on its own (it would
     * reject {@code "usd"}), whereas the Python port up-cases the code, so without this
     * normalisation the two sides would disagree on lower-case input.
     */
    public static Money of(BigDecimal amount, String currencyCode) {
        Objects.requireNonNull(amount, "amount");
        Objects.requireNonNull(currencyCode, "currencyCode");
        Currency currency = Currency.getInstance(currencyCode.toUpperCase(java.util.Locale.ROOT));
        BigDecimal scaled = amount.setScale(currency.getDefaultFractionDigits(), RoundingMode.HALF_EVEN);
        return new Money(scaled, currency);
    }

    public static Money of(String amount, String currencyCode) {
        return of(new BigDecimal(amount), currencyCode);
    }

    /** Add another Money of the SAME currency. Throws on a currency mismatch. */
    public Money add(Money other) {
        requireSameCurrency(other);
        return new Money(this.amount.add(other.amount), this.currency);
    }

    /** Subtract another Money of the SAME currency. Throws on a currency mismatch. */
    public Money subtract(Money other) {
        requireSameCurrency(other);
        return new Money(this.amount.subtract(other.amount), this.currency);
    }

    /**
     * Multiply by an integer quantity (e.g. unit price x N items). Exact: no rounding
     * is introduced because the scale is already fixed and the factor is an integer.
     */
    public Money multiply(long factor) {
        return new Money(this.amount.multiply(BigDecimal.valueOf(factor)), this.currency);
    }

    /**
     * Apply a percentage rate (e.g. a 7.5% tax) and round the result back to the
     * currency scale with HALF_EVEN. The rate is a plain BigDecimal like 0.075.
     */
    public Money percentage(BigDecimal rate) {
        BigDecimal raw = this.amount.multiply(rate);
        BigDecimal scaled = raw.setScale(currency.getDefaultFractionDigits(), RoundingMode.HALF_EVEN);
        return new Money(scaled, this.currency);
    }

    private void requireSameCurrency(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException(
                    "currency mismatch: " + this.currency + " vs " + other.currency);
        }
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public Currency getCurrency() {
        return currency;
    }

    /**
     * Value equality: two Money are equal iff the currency matches AND the amount is
     * numerically equal at the same scale. Uses compareTo (not BigDecimal.equals,
     * which also compares scale) after both have been scale-normalised in {@code of}.
     */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Money)) return false;
        Money money = (Money) o;
        return currency.equals(money.currency) && amount.compareTo(money.amount) == 0;
    }

    @Override
    public int hashCode() {
        return Objects.hash(amount.stripTrailingZeros(), currency);
    }

    @Override
    public String toString() {
        return amount.toPlainString() + " " + currency.getCurrencyCode();
    }
}
