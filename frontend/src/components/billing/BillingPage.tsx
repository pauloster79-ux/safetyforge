import { Check, Zap, Loader2, CreditCard, ArrowRight, Clock } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useCompany, useSubscription, useUpgradeSubscription } from '@/hooks/useCompany';
import { SUBSCRIPTION_TIERS } from '@/lib/constants';
import { cn } from '@/lib/utils';

export function BillingPage() {
  const { data: company } = useCompany();
  const { data: subscription, isLoading } = useSubscription();
  const upgradeSubscription = useUpgradeSubscription();

  const currentPlanId = (subscription?.plan_name || 'free').toLowerCase();
  const subscriptionStatus = subscription?.status || company?.subscription_status || 'free';

  const handleUpgrade = (tierId: string) => {
    upgradeSubscription.mutate(tierId);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Billing & Subscription</h1>
        <p className="text-sm text-muted-foreground">
          Manage your subscription plan and billing details
        </p>
      </div>

      {subscription?.is_trial && subscription.trial_days_remaining != null && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="flex items-center gap-3 py-4">
            <Clock className="h-5 w-5 text-primary flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-foreground">
                {subscription.trial_days_remaining > 0
                  ? `${subscription.trial_days_remaining} day${subscription.trial_days_remaining !== 1 ? 's' : ''} left in your free trial`
                  : 'Your free trial has ended'}
              </p>
              <p className="text-xs text-muted-foreground">
                {subscription.trial_days_remaining > 0
                  ? 'Upgrade to keep full access to all features after your trial ends.'
                  : 'Upgrade now to continue using Kerf.'}
              </p>
            </div>
            <Button
              size="sm"
              className="bg-primary hover:bg-[var(--machine-dark)] flex-shrink-0"
              onClick={() => handleUpgrade('professional')}
              disabled={upgradeSubscription.isPending}
            >
              Upgrade Now
            </Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Current Plan</CardTitle>
              <CardDescription>
                Your current subscription status
              </CardDescription>
            </div>
            <Badge
              className={cn(
                'text-sm',
                subscriptionStatus === 'active'
                  ? 'bg-[var(--pass-bg)] text-[var(--pass)]'
                  : subscriptionStatus === 'past_due'
                    ? 'bg-[var(--fail-bg)] text-[var(--fail)]'
                    : 'bg-muted text-[var(--concrete-600)]'
              )}
            >
              {subscription?.plan_name || 'Free'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 sm:grid-cols-3">
            <div>
              <p className="text-sm text-muted-foreground">Status</p>
              <p className="mt-1 text-lg font-semibold capitalize text-foreground">
                {subscriptionStatus}
              </p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Max Projects</p>
              <p className="mt-1 text-lg font-semibold text-foreground">
                {subscription?.max_projects === -1
                  ? 'Unlimited'
                  : subscription?.max_projects ?? 1}
              </p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Renewal</p>
              <p className="mt-1 text-lg font-semibold text-foreground">
                {subscription?.renewal_date
                  ? new Date(subscription.renewal_date).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })
                  : 'N/A'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">Available Plans</h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {SUBSCRIPTION_TIERS.map((tier) => {
            const isCurrentPlan = tier.id === currentPlanId;
            const isPopular = tier.id === 'professional';

            return (
              <Card
                key={tier.id}
                className={cn(
                  'relative flex flex-col',
                  isPopular && 'border-primary shadow-md',
                  isCurrentPlan && 'bg-muted'
                )}
              >
                {isPopular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="bg-primary text-primary-foreground hover:bg-primary">
                      <Zap className="mr-1 h-3 w-3" />
                      Most Popular
                    </Badge>
                  </div>
                )}

                <CardHeader className="text-center">
                  <CardTitle className="text-xl">{tier.name}</CardTitle>
                  <div className="mt-2">
                    {tier.price === -1 ? (
                      <span className="text-3xl font-bold text-foreground">Custom</span>
                    ) : (
                      <>
                        <span className="text-4xl font-bold text-foreground">
                          ${tier.price}
                        </span>
                        <span className="text-sm text-muted-foreground">/month</span>
                      </>
                    )}
                  </div>
                  <CardDescription>
                    {tier.maxProjects === -1
                      ? 'Unlimited projects'
                      : `${tier.maxProjects} projects`}
                  </CardDescription>
                </CardHeader>

                <CardContent className="flex flex-1 flex-col">
                  <Separator className="mb-4" />

                  <ul className="flex-1 space-y-3">
                    {tier.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-2">
                        <Check className="mt-0.5 h-4 w-4 shrink-0 text-[var(--pass)]" />
                        <span className="text-sm text-muted-foreground">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <div className="mt-6">
                    {isCurrentPlan ? (
                      <Button variant="outline" className="w-full" disabled>
                        Current Plan
                      </Button>
                    ) : tier.price === -1 ? (
                      <Button
                        className="w-full bg-[var(--concrete-800)] hover:bg-[var(--concrete-700)]"
                        onClick={() => handleUpgrade(tier.id)}
                        disabled={upgradeSubscription.isPending}
                      >
                        Contact Sales
                      </Button>
                    ) : (
                      <Button
                        className={cn(
                          'w-full',
                          isPopular
                            ? 'bg-primary hover:bg-[var(--machine-dark)]'
                            : 'bg-[var(--concrete-800)] hover:bg-[var(--concrete-700)]'
                        )}
                        onClick={() => handleUpgrade(tier.id)}
                        disabled={upgradeSubscription.isPending}
                      >
                        {upgradeSubscription.isPending ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <ArrowRight className="mr-2 h-4 w-4" />
                        )}
                        Upgrade to {tier.name}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">Payment Method</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between rounded-lg border border-border p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-14 items-center justify-center rounded-md bg-muted">
                <CreditCard className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium text-[var(--concrete-600)]">No payment method on file</p>
                <p className="text-xs text-muted-foreground">Add a payment method to upgrade your plan</p>
              </div>
            </div>
            <Button variant="outline" size="sm">
              Add Card
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
