import { Header } from "@/components/landing/header";
import { Footer } from "@/components/landing/footer";
import { Hero } from "@/components/landing/hero";

export default function LandingPage() {
  return (
      <div className="min-h-screen w-full bg-[#0a0a0a]">
        <Header />
        <main className="flex w-full flex-col">
          <Hero />
        {/*  <CaseStudySection />*/}
        {/*  <SkillsSection />*/}
        {/*  <SandboxSection />*/}
        {/*  <WhatsNewSection />*/}
        {/*  <CommunitySection />*/}
        </main>
        <Footer />
      </div>
  );
}
